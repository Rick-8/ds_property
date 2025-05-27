import json
import logging
import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Prefetch
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST


from .models import ServicePackage, ServiceAgreement
from accounts.models import Property
from django.contrib.auth import get_user_model

User = get_user_model()

logger = logging.getLogger(__name__)


stripe.api_key = settings.STRIPE_SECRET_KEY


def is_staff(user):
    return user.is_staff


@login_required
def package_selection(request):
    """
    Displays available service packages and user's properties.
    Properties are prefetched with their active service agreements.
    """
    packages = ServicePackage.objects.all().order_by('price_per_month')

    user_properties = Property.objects.filter(
        profile__user=request.user,
        is_active=True
    ).prefetch_related(
        Prefetch(
            'serviceagreement_set',
            queryset=ServiceAgreement.objects.filter(active=True),
            to_attr='active_agreements'
        )
    )

    for prop in user_properties:
        prop.has_active_agreement = bool(prop.active_agreements)
        if prop.has_active_agreement:
            prop.current_package_name = prop.active_agreements[0].service_package.name
        else:
            prop.current_package_name = None

    context = {
        'packages': packages,
        'user_properties': user_properties,
    }
    return render(request, 'memberships/package_selection.html', context)


@login_required
@csrf_protect
def payment(request, package_id):
    """
    Handles displaying the payment form (GET) and processing subscription creation (POST).
    """
    package = get_object_or_404(ServicePackage, pk=package_id)

    if not package.stripe_price_id:
        messages.error(request, "Sorry, this package is not configured properly for payment. Please contact support.")
        return redirect("package_selection")

    property_id = request.GET.get("property_id")
    property_obj = None
    if property_id:
        property_obj = get_object_or_404(Property, pk=property_id, profile__user=request.user, is_active=True)
    else:
        messages.error(request, "No property selected for this service package.")
        return redirect("package_selection")

    if request.method == "POST":
        payment_method_id = request.POST.get("payment_method_id")
        if not payment_method_id:
            return JsonResponse({"error": "Missing payment_method_id"}, status=400)

        if not property_obj:
            return JsonResponse({"error": "No property associated with this payment request."}, status=400)

        try:
            if not hasattr(request.user, "stripe_customer_id") or not request.user.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=request.user.email,
                    name=request.user.get_full_name() or request.user.username,
                    metadata={
                        'django_user_id': str(request.user.id),
                        'django_username': request.user.username,
                    }
                )
                request.user.stripe_customer_id = customer.id
                request.user.save()
                logger.info(f"Stripe Customer created for user {request.user.id}: {customer.id}")
            else:
                customer = stripe.Customer.retrieve(request.user.stripe_customer_id)
                logger.info(f"Stripe Customer retrieved for user {request.user.id}: {customer.id}")

            stripe.PaymentMethod.attach(payment_method_id, customer=customer.id)
            stripe.Customer.modify(
                customer.id,
                invoice_settings={"default_payment_method": payment_method_id},
            )
            logger.info(f"PaymentMethod {payment_method_id} attached and set as default for customer {customer.id}")

            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{'price': package.stripe_price_id}],
                default_payment_method=payment_method_id,
                expand=['latest_invoice.payment_intent'],
                metadata={
                    'user_id': str(request.user.id),
                    'property_id': str(property_obj.id),
                    'package_name': package.name,
                    'package_id': str(package.id),
                }
            )
            logger.info(f"Stripe Subscription created: {subscription.id}")

            if subscription.latest_invoice and subscription.latest_invoice.payment_intent:
                payment_intent = subscription.latest_invoice.payment_intent
                if payment_intent.status == 'requires_action' or payment_intent.status == 'requires_confirmation':
                    return JsonResponse({
                        'requires_action': True,
                        'payment_intent_client_secret': payment_intent.client_secret
                    })
                elif payment_intent.status == 'succeeded':
                    messages.success(request, "Subscription successful! Your service is active.")
                    return JsonResponse({'success_url': reverse("subscription_success")})
                else:
                    logger.warning(f"Payment Intent status unexpected: {payment_intent.status} for subscription {subscription.id}")
                    return JsonResponse({"error": f"Payment status: {payment_intent.status}. Please check Stripe dashboard or contact support."}, status=400)
            else:
                messages.success(request, "Subscription started! We'll notify you when the first payment is due.")
                return JsonResponse({'success_url': reverse("subscription_success")})

        except stripe.error.CardError as e:
            logger.error(f"Stripe Card Error: {e.user_message}", exc_info=True)
            return JsonResponse({"error": e.user_message}, status=400)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe API Error in payment view: {e}", exc_info=True)
            return JsonResponse({"error": str(e)}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error in payment view: {e}", exc_info=True)
            return JsonResponse({"error": "An unexpected error occurred during payment processing."}, status=500)

    context = {
        "package": package,
        "property": property_obj,
        "stripe_publishable_key": settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, "memberships/payment.html", context)


@login_required
def subscription_success(request):
    """
    Page displayed after a successful subscription.
    """
    messages.success(request, "Your subscription has been successfully set up!")
    return render(request, 'memberships/subscription_success.html')


@login_required
def subscription_cancel(request):
    """
    Page displayed if subscription process is cancelled.
    """
    messages.info(request, "Your subscription setup was cancelled.")
    return render(request, 'memberships/subscription_cancel.html')


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        logger.info(f"🔔 Received event: {event['type']}")
    except ValueError as e:
        logger.error(f"⚠️ Invalid payload: {e}", exc_info=True)
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"⚠️ Invalid signature: {e}", exc_info=True)
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"⚠️ Unexpected error constructing Stripe event: {e}", exc_info=True)
        return HttpResponse(status=500)

    if event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        logger.info(f"✅ Webhook: Processing customer.subscription.created event for subscription {subscription['id']}")

        metadata = subscription.get('metadata', {})
        user_id = metadata.get('user_id')
        property_id = metadata.get('property_id')
        package_name = metadata.get('package_name')
        subscription_id = subscription.get('id')

        if not all([user_id, property_id, package_name, subscription_id]):
            logger.warning(f"⚠️ Missing required metadata in customer.subscription.created: user_id({user_id}), property_id({property_id}), package_name({package_name}), subscription_id({subscription_id}).")
            return HttpResponse(status=400)

        try:
            user = User.objects.get(id=user_id)
            prop = Property.objects.get(id=property_id)
            service_package = ServicePackage.objects.get(name=package_name)

            prop.has_active_service = True
            prop.stripe_subscription_id = subscription_id
            prop.save()
            logger.info(f"✅ Property {property_id} marked active with subscription {subscription_id}.")

            agreement, created = ServiceAgreement.objects.get_or_create(
                stripe_subscription_id=subscription_id,
                defaults={
                    'user': user,
                    'service_package': service_package,
                    'property': prop,
                    'active': True,
                    'start_date': timezone.now().date(),
                }
            )

            if not created:
                agreement.user = user
                agreement.service_package = service_package
                agreement.property = prop
                agreement.active = True
                agreement.save()
                logger.info(f"ℹ️ Existing ServiceAgreement for subscription {subscription_id} updated (was not created).")
            else:
                logger.info("✅ ServiceAgreement created successfully.")

        except User.DoesNotExist:
            logger.error(f"❌ User {user_id} not found for subscription {subscription_id}.")
            return HttpResponse(status=400)
        except Property.DoesNotExist:
            logger.error(f"❌ Property {property_id} not found for subscription {subscription_id}.")
            return HttpResponse(status=400)
        except ServicePackage.DoesNotExist:
            logger.error(f"❌ ServicePackage '{package_name}' not found for subscription {subscription_id}.")
            return HttpResponse(status=400)
        except Exception as e:
            logger.error(f"❌ Error processing customer.subscription.created: {e}", exc_info=True)
            return HttpResponse(status=400)

    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        subscription_id = invoice.get('subscription')
        if subscription_id:
            logger.info(f"✅ Webhook: Received invoice.payment_succeeded for subscription {subscription_id}.")

            try:
                subscription = stripe.Subscription.retrieve(subscription_id)
                metadata = subscription.get('metadata', {})
                user_id = metadata.get('user_id')
                property_id = metadata.get('property_id')
                package_name = metadata.get('package_name')

                if not all([user_id, property_id, package_name]):
                    logger.warning(f"⚠️ Missing required metadata in invoice.payment_succeeded for subscription {subscription_id}.")
                    return HttpResponse(status=400)

                prop = Property.objects.get(id=property_id)
                user = User.objects.get(id=user_id)
                service_package = ServicePackage.objects.get(name=package_name)

                prop.has_active_service = True
                prop.stripe_subscription_id = subscription_id
                prop.save()

                agreement, created = ServiceAgreement.objects.get_or_create(
                    stripe_subscription_id=subscription_id,
                    defaults={
                        'user': user,
                        'service_package': service_package,
                        'property': prop,
                        'active': True,
                        'start_date': timezone.now().date(),
                    }
                )
                if not created:
                    agreement.active = True
                    agreement.user = user
                    agreement.service_package = service_package
                    agreement.property = prop
                    agreement.end_date = None
                    agreement.save()
                    logger.info(f"✅ Existing ServiceAgreement for subscription {subscription_id} updated/confirmed active via invoice.payment_succeeded.")
                else:
                    logger.info("✅ ServiceAgreement created via invoice.payment_succeeded (unlikely for first payment if customer.subscription.created is handled).")

            except (User.DoesNotExist, Property.DoesNotExist, ServicePackage.DoesNotExist) as e:
                logger.error(f"❌ Related object not found for invoice.payment_succeeded: {e}", exc_info=True)
                return HttpResponse(status=400)
            except Exception as e:
                logger.error(f"❌ Error processing invoice.payment_succeeded: {e}", exc_info=True)
                return HttpResponse(status=400)
        else:
            logger.info("ℹ️ Invoice payment succeeded for non-subscription invoice or subscription ID missing. Skipping.")

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        subscription_id = subscription.get('id')
        logger.info(f"🚫 Webhook: Received customer.subscription.deleted event for subscription {subscription_id}")
        try:

            agreement = ServiceAgreement.objects.get(stripe_subscription_id=subscription_id)
            agreement.active = False
            agreement.end_date = timezone.now().date()
            agreement.save()
            logger.info(f"✅ ServiceAgreement for subscription {subscription_id} marked inactive and end_date set.")

            prop = agreement.property
            if not ServiceAgreement.objects.filter(property=prop, active=True).exists():
                prop.has_active_service = False
                prop.stripe_subscription_id = None
                prop.save()
                logger.info(f"✅ Property {prop.id} marked inactive as no active agreements remain.")
            else:
                logger.info(f"ℹ️ Property {prop.id} remains active as other agreements exist.")

        except ServiceAgreement.DoesNotExist:
            logger.warning(f"⚠️ ServiceAgreement not found for deleted subscription {subscription_id}. Might be a duplicate delete event or unmatched ID.")
        except Exception as e:
            logger.error(f"❌ Error processing customer.subscription.deleted: {e}", exc_info=True)
            return HttpResponse(status=400)

    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        subscription_id = subscription.get('id')
        logger.info(f"🔄 Webhook: Received customer.subscription.updated event for subscription {subscription_id}")

        if subscription.get('status') == 'active':
            try:
                agreement = ServiceAgreement.objects.get(stripe_subscription_id=subscription_id)
                if not agreement.active:
                    agreement.active = True
                    agreement.end_date = None
                    agreement.save()
                    logger.info(f"✅ ServiceAgreement for subscription {subscription_id} reactivated via update.")
            except ServiceAgreement.DoesNotExist:
                logger.warning(f"⚠️ ServiceAgreement not found for updated active subscription {subscription_id}.")
            except Exception as e:
                logger.error(f"❌ Error processing customer.subscription.updated (active status): {e}", exc_info=True)
                return HttpResponse(status=400)
        elif subscription.get('status') in ['canceled', 'unpaid', 'incomplete', 'past_due']:
            try:
                agreement = ServiceAgreement.objects.get(stripe_subscription_id=subscription_id)
                if agreement.active:
                    agreement.active = False
                    agreement.end_date = timezone.now().date()
                    agreement.save()
                    logger.info(f"🚫 ServiceAgreement for subscription {subscription_id} marked inactive due to status '{subscription.get('status')}'.")
                    prop = agreement.property
                    if not ServiceAgreement.objects.filter(property=prop, active=True).exists():
                        prop.has_active_service = False
                        prop.stripe_subscription_id = None
                        prop.save()
                        logger.info(f"✅ Property {prop.id} marked inactive as no active agreements remain after update.")
            except ServiceAgreement.DoesNotExist:
                logger.warning(f"⚠️ ServiceAgreement not found for updated inactive subscription {subscription_id}.")
            except Exception as e:
                logger.error(f"❌ Error processing customer.subscription.updated (inactive status): {e}", exc_info=True)
                return HttpResponse(status=400)
        else:
            logger.info(f"ℹ️ customer.subscription.updated event for status '{subscription.get('status')}' received. No specific action taken.")

    elif event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        logger.info("✅ Webhook: Received checkout.session.completed event.")
        if session.get('mode') == 'subscription':
            logger.warning("⚠️ Received checkout.session.completed for subscription mode, but expected customer.subscription.created. Double-check integration.")
        else:
            logger.info(f"ℹ️ checkout.session.completed for non-subscription mode: {session.get('mode')}. Skipping.")

    else:
        logger.info(f"ℹ️ Unhandled event type: {event['type']}")

    return HttpResponse(status=200)
