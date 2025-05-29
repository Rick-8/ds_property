import json
import logging
import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Prefetch
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST
from django.db import transaction

from .models import ServiceAgreement, ServicePackage
from .forms import ServicePackageForm
from accounts.models import Property, Profile

# Email imports
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

User = get_user_model()

logger = logging.getLogger(__name__)

# Set Stripe API key from Django settings
stripe.api_key = settings.STRIPE_SECRET_KEY


def superuser_required(view_func):
    """
    Decorator to restrict access to superusers only.
    """
    return user_passes_test(lambda u: u.is_superuser)(view_func)


def staff_or_superuser_required(user):
    """
    Helper function for user_passes_test to check if user is staff or superuser.
    """
    return user.is_staff or user.is_superuser


def servicepackage_list(request):
    """
    Lists all service packages. This might be a public or admin view.
    """
    packages = ServicePackage.objects.all()
    category = "Silver"
    return render(request, "memberships/list.html", {
        "packages": packages,
        "category": category,
    })


@superuser_required
def package_create(request):
    """
    Allows superusers to create new service packages.
    """
    if request.method == 'POST':
        form = ServicePackageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Service package created successfully!")
            return redirect('servicepackage_list')
    else:
        form = ServicePackageForm()
    return render(request, 'memberships/form.html', {'form': form, 'title': 'Create Service Package'})


@superuser_required
def package_update(request, pk):
    """
    Allows superusers to update existing service packages.
    """
    package = get_object_or_404(ServicePackage, pk=pk)
    if request.method == 'POST':
        form = ServicePackageForm(request.POST, instance=package)
        if form.is_valid():
            form.save()
            messages.success(request, "Service package updated successfully!")
            return redirect('servicepackage_list')
    else:
        form = ServicePackageForm(instance=package)
    return render(request, 'memberships/form.html', {'form': form, 'title': 'Update Service Package'})


@superuser_required
def package_delete(request, pk):
    """
    Allows superusers to delete service packages.
    """
    package = get_object_or_404(ServicePackage, pk=pk)
    if request.method == 'POST':
        package.delete()
        messages.success(request, "Service package deleted successfully!")
        return redirect('servicepackage_list')
    return render(request, 'memberships/confirm_delete.html', {'package': package})


@login_required
def package_selection(request):
    """
    Displays available service packages for user selection, along with their properties.
    This view prefetches active agreements for properties to show their status.
    """
    packages = ServicePackage.objects.filter(is_active=True).order_by('price_usd')

    # Fetch user's active properties and prefetch their active service agreements
    user_properties = Property.objects.filter(
        profile__user=request.user,
        is_active=True
    ).prefetch_related(
        # Prefetch ServiceAgreement objects related to each property
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
@require_POST
def select_package(request, package_id):
    """
    Handles AJAX request to add a package to the session's 'selected_packages'.
    Includes server-side validation to prevent selecting a property with an existing active agreement.
    """
    package = get_object_or_404(ServicePackage, id=package_id, is_active=True)

    property_id = request.POST.get('property_id')

    selected_packages = request.session.get('selected_packages', {})

    package_data = {
        'id': package.id,
        'name': package.name,
        'category': package.get_category_display(),
        'tier': package.get_tier_display(),
        'price_usd': float(package.price_usd),
        'property_id': None,
        'property_label': None,
        'property_address_summary': None,
    }

    if property_id:
        try:
            selected_property = Property.objects.get(id=property_id, profile__user=request.user, is_active=True)

            if ServiceAgreement.objects.filter(property=selected_property, active=True).exists():
                return JsonResponse({'success': False, 'error': 'This property already has an active service agreement. Please choose another property or cancel the existing service.'}, status=400)

            package_data['property_id'] = selected_property.id
            package_data['property_label'] = selected_property.label
            package_data['property_address_summary'] = selected_property.address_summary

        except Property.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Selected property is invalid or does not belong to you.'}, status=400)

    selected_packages[package.category] = package_data
    request.session['selected_packages'] = selected_packages
    request.session.modified = True

    messages.success(request, f"'{package.name}' added to your selection.")
    return JsonResponse({'success': True, 'package': package_data})


@login_required
@require_POST
def update_package_property(request, package_id):
    """
    Updates the property associated with a package in the session's 'selected_packages'.
    Includes server-side validation for property conflicts.
    """
    try:
        data = json.loads(request.body)
        property_id = data.get('property_id')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON request.'}, status=400)

    selected_packages = request.session.get('selected_packages', {})
    category_key = None

    for category, pkg_data in selected_packages.items():
        if str(pkg_data.get('id')) == str(package_id):
            category_key = category
            break

    if not category_key:
        return JsonResponse({'success': False, 'error': 'Package not found in session.'}, status=404)

    service_package_obj = get_object_or_404(ServicePackage, pk=package_id)

    if property_id:
        try:
            selected_property = Property.objects.get(id=property_id, profile__user=request.user, is_active=True)

            existing_active_agreements = ServiceAgreement.objects.filter(property=selected_property, active=True)

            if existing_active_agreements.exists():
                is_current_package_agreement = False
                for agreement in existing_active_agreements:
                    if agreement.service_package == service_package_obj:
                        is_current_package_agreement = True
                        break

                if not is_current_package_agreement:
                    conflict_package_name = existing_active_agreements.first().service_package.name
                    return JsonResponse({'success': False, 'error': f'This property already has an active service agreement with {conflict_package_name}. Please choose another property or cancel the existing service.'}, status=400)

            selected_packages[category_key]['property_id'] = selected_property.id
            selected_packages[category_key]['property_label'] = selected_property.label
            selected_packages[category_key]['property_address_summary'] = selected_property.address_summary
            messages.success(request, f"Package {selected_packages[category_key]['name']} now associated with {selected_property.label}.")

        except Property.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Selected property is invalid or does not belong to you.'}, status=400)
    else:
        selected_packages[category_key]['property_id'] = None
        selected_packages[category_key]['property_label'] = None
        selected_packages[category_key]['property_address_summary'] = None
        messages.info(request, "Property association removed for selected package.")

    request.session['selected_packages'] = selected_packages
    request.session.modified = True

    return JsonResponse({'success': True, 'package': selected_packages[category_key]})


@login_required
def confirm_contract(request, package_id):
    """
    Displays contract details before payment for a selected package.
    Includes server-side re-validation for property conflicts.
    """
    package = get_object_or_404(ServicePackage, pk=package_id)
    property_id = request.GET.get('property_id')
    property_obj = None

    if property_id:
        property_obj = get_object_or_404(Property, pk=property_id, profile__user=request.user)

        if ServiceAgreement.objects.filter(property=property_obj, active=True).exclude(service_package=package).exists():
            messages.error(request, "This property already has an active service agreement with a different package. Please choose another property or cancel the existing service.")
            return redirect(reverse('package_selection'))

    selected_packages = request.session.get('selected_packages', {})

    context = {
        'package': package,
        'property': property_obj,
        'selected_packages': selected_packages,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    }

    print(f"DEBUG: In confirm_contract view, settings.STRIPE_PUBLISHABLE_KEY = '{settings.STRIPE_PUBLISHABLE_KEY}'")

    return render(request, 'memberships/confirm_contract.html', context)


@login_required
@csrf_protect
@require_POST
def payment(request, package_id):
    """
    Handles processing subscription creation using Stripe's Subscription API directly.
    This view expects a POST request with 'payment_method_id' and 'property_id' in JSON body.
    Includes a final critical check for active agreements and now creates/updates Django models.
    """
    package = get_object_or_404(ServicePackage, pk=package_id)

    if not package.stripe_price_id:
        messages.error(request, "Sorry, this package is not configured properly for payment. Please contact support.")
        return JsonResponse({"error": "Package not configured for Stripe."}, status=400)

    try:
        data = json.loads(request.body)
        payment_method_id = data.get('payment_method_id')
        property_id = data.get('property_id')

    except json.JSONDecodeError:
        logger.error("Invalid JSON in payment request body.", exc_info=True)
        return JsonResponse({"error": "Invalid request format."}, status=400)

    print(f"DEBUG: payment view - Received property_id from JSON: {property_id}")
    print(f"DEBUG: payment view - Received payment_method_id from JSON: {payment_method_id}")

    property_obj = None
    if property_id:
        try:
            property_obj = Property.objects.get(pk=property_id, profile__user=request.user, is_active=True)
        except Property.DoesNotExist:
            logger.warning(f"Property {property_id} not found or not active for user {request.user.id}")
            return JsonResponse({"error": "Invalid property selected."}, status=400)
    else:
        logger.warning(f"No property_id received in payment request for user {request.user.id}")
        return JsonResponse({"error": "No property selected for this service package."}, status=400)

    existing_agreement = ServiceAgreement.objects.filter(
        property=property_obj,
        active=True
    ).first()

    if existing_agreement:
        if existing_agreement.service_package == package:
            messages.info(request, f"This property already has an active '{package.name}' service agreement. No new subscription created.")
            return JsonResponse({'success_url': reverse("subscription_success")})
        else:
            messages.error(request, f"This property already has an active '{existing_agreement.service_package.name}' service agreement. Please cancel it first or choose another property.")
            return JsonResponse({"error": "This property already has an active service agreement with a different package."}, status=400)

    if not payment_method_id:
        logger.warning(f"Missing payment_method_id for user {request.user.id}")
        return JsonResponse({"error": "Missing payment_method_id"}, status=400)

    try:
        if not hasattr(request.user, "profile") or not request.user.profile.stripe_customer_id:
            customer = stripe.Customer.create(
                email=request.user.email,
                name=request.user.get_full_name() or request.user.username,
                metadata={
                    'django_user_id': str(request.user.id),
                    'django_username': request.user.username,
                }
            )
            request.user.profile.stripe_customer_id = customer.id
            request.user.profile.save()
            logger.info(f"Stripe Customer created for user {request.user.id}: {customer.id}")
        else:
            customer = stripe.Customer.retrieve(request.user.profile.stripe_customer_id)
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
            expand=['latest_invoice'],
            metadata={
                'user_id': str(request.user.id),
                'property_id': str(property_obj.id),
                'package_name': package.name,
                'package_id': str(package.id),
            }
        )
        logger.info(f"Stripe Subscription created: {subscription.id}")

        with transaction.atomic():
            ServiceAgreement.objects.create(
                user=request.user,
                service_package=package,
                property=property_obj,
                start_date=timezone.now(),
                status='active',
                stripe_subscription_id=subscription.id,
                stripe_customer_id=customer.id,
                stripe_price_id=package.stripe_price_id,
                amount_paid=package.price_usd,
                active=True
            )
            logger.info(f"Django ServiceAgreement created for Stripe subscription {subscription.id}")

            property_obj.is_subscribed = True
            property_obj.save()
            logger.info(f"Property {property_obj.id} status updated to is_subscribed=True.")

        if subscription.latest_invoice:
            payment_intent = subscription.latest_invoice.get('payment_intent')

            if payment_intent:
                if payment_intent.status == 'requires_action' or payment_intent.status == 'requires_confirmation':
                    return JsonResponse({
                        'requires_action': True,
                        'payment_intent_client_secret': payment_intent.client_secret,
                        'success_url': reverse("subscription_success")
                    })
                elif payment_intent.status == 'succeeded':
                    messages.success(request, "Subscription successful! Your service is active.")
                    if 'selected_packages' in request.session:
                        del request.session['selected_packages']
                    return JsonResponse({'success_url': reverse("subscription_success")})
                else:
                    logger.warning(f"Payment Intent status unexpected: {payment_intent.status} for subscription {subscription.id}")
                    return JsonResponse({"error": f"Payment status: {payment_intent.status}. Please check Stripe dashboard or contact support."}, status=400)
            else:
                messages.success(request, "Subscription started! We'll notify you when the first payment is due.")
                if 'selected_packages' in request.session:
                    del request.session['selected_packages']
                return JsonResponse({'success_url': reverse("subscription_success")})
        else:
            messages.success(request, "Subscription started! We'll notify you when the first payment is due.")
            if 'selected_packages' in request.session:
                del request.session['selected_packages']
            return JsonResponse({'success_url': reverse("subscription_success")})

    except stripe.error.CardError as e:
        logger.error(f"Stripe Card Error in payment view: {e.user_message}", exc_info=True)
        return JsonResponse({"error": e.user_message}, status=400)
    except stripe.error.StripeError as e:
        logger.error(f"Stripe API Error in payment view: {e}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in payment view: {e}", exc_info=True)
        return JsonResponse({"error": "An unexpected error occurred during payment processing."}, status=500)


@login_required
def subscription_success(request):
    """
    Page displayed after a successful subscription.
    """
    return render(request, 'memberships/subscription_success.html')


@login_required
def subscription_cancel(request):
    """
    Page displayed if subscription process is cancelled (e.g., user navigates away).
    """
    messages.info(request, "Your subscription setup was cancelled.")
    return render(request, 'memberships/subscription_cancel.html')


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Handles Stripe webhook events to update ServiceAgreement and Property models.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        logger.info(f"🔔 Received event: {event['type']}")
    except ValueError as e:
        # Invalid payload
        logger.error(f"⚠️ Invalid payload: {e}", exc_info=True)
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"⚠️ Invalid signature: {e}", exc_info=True)
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"⚠️ Unexpected error constructing Stripe event: {e}", exc_info=True)
        return HttpResponse(status=500)

    # Handle event types
    if event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        logger.info(f"✅ Webhook: Processing customer.subscription.created event for subscription {subscription['id']}")

        metadata = subscription.get('metadata', {})
        user_id = metadata.get('user_id')
        property_id = metadata.get('property_id')
        package_id = metadata.get('package_id')

        # Ensure all required metadata is present
        if not all([user_id, property_id, package_id, subscription['id']]):
            logger.warning(f"⚠️ Missing required metadata in customer.subscription.created: user_id({user_id}), property_id({property_id}), package_id({package_id}), subscription_id({subscription['id']}).")
            return HttpResponse(status=400)

        try:
            user = User.objects.get(id=user_id)
            prop = Property.objects.get(id=property_id)
            service_package = ServicePackage.objects.get(id=package_id)

            # CRITICAL: Deactivate any existing active agreements for this property
            # This ensures only one agreement is active per property at any given time.
            ServiceAgreement.objects.filter(property=prop, active=True).update(active=False, end_date=timezone.now().date())
            logger.info(f"ℹ️ Deactivated previous active agreements for property {prop.id}.")

            # Create or update the ServiceAgreement
            agreement, created = ServiceAgreement.objects.get_or_create(
                stripe_subscription_id=subscription['id'],
                defaults={
                    'user': user,
                    'service_package': service_package,
                    'property': prop,
                    'active': True,
                    'start_date': timezone.now().date(),
                    'stripe_customer_id': subscription['customer'],
                    'stripe_current_period_end': timezone.datetime.fromtimestamp(
                        subscription['current_period_end'], tz=timezone.utc
                    ).date() if 'current_period_end' in subscription else None,
                }
            )

            if not created:
                # If agreement already existed (e.g., webhook retry), ensure it's up-to-date
                agreement.user = user
                agreement.service_package = service_package
                agreement.property = prop
                agreement.active = True
                agreement.start_date = timezone.now().date()
                agreement.stripe_customer_id = subscription['customer']
                agreement.stripe_current_period_end = timezone.datetime.fromtimestamp(
                    subscription['current_period_end'], tz=timezone.utc
                ).date() if 'current_period_end' in subscription else None
                agreement.save()
                logger.info(f"ℹ️ Existing ServiceAgreement for subscription {subscription['id']} updated (was not created).")
            else:
                logger.info(f"✅ ServiceAgreement created successfully for subscription {subscription['id']}.")

            prop.stripe_subscription_id = subscription['id']
            prop.has_active_service = True
            prop.save()
            logger.info(f"✅ Property {prop.id} marked active with subscription {subscription['id']}.")

        except User.DoesNotExist:
            logger.error(f"❌ Webhook Error: User {user_id} not found for subscription {subscription['id']}.")
            return HttpResponse(status=400)
        except Property.DoesNotExist:
            logger.error(f"❌ Webhook Error: Property {property_id} not found for subscription {subscription['id']}.")
            return HttpResponse(status=400)
        except ServicePackage.DoesNotExist:
            logger.error(f"❌ Webhook Error: ServicePackage {package_id} not found for subscription {subscription['id']}.")
            return HttpResponse(status=400)
        except Exception as e:
            logger.error(f"❌ Unexpected error in customer.subscription.created webhook: {e}", exc_info=True)
            return HttpResponse(status=400)

    elif event['type'] == 'customer.subscription.deleted' or event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        logger.info(f"✅ Webhook: Processing {event['type']} event for subscription {subscription['id']}")

        try:
            agreement = ServiceAgreement.objects.get(stripe_subscription_id=subscription['id'])

            # Update agreement status based on Stripe subscription status
            if subscription['status'] == 'canceled':
                agreement.active = False
                agreement.end_date = timezone.now().date()
                logger.info(f"ℹ️ ServiceAgreement {agreement.id} marked as inactive due to cancellation.")
            elif subscription['status'] == 'active':
                agreement.active = True
                agreement.stripe_current_period_end = timezone.datetime.fromtimestamp(
                    subscription['current_period_end'], tz=timezone.utc
                ).date() if 'current_period_end' in subscription else None
                logger.info(f"ℹ️ ServiceAgreement {agreement.id} updated to active.")
            else:
                # For any other non-active status, set to inactive
                logger.warning(f"⚠️ Unhandled subscription status '{subscription['status']}' for agreement {agreement.id}. Marking as inactive.")
                agreement.active = False

            agreement.save()

            if agreement.property:
                other_active_agreements = ServiceAgreement.objects.filter(
                    property=agreement.property,
                    active=True
                ).exclude(id=agreement.id).exists()

                if not other_active_agreements and not agreement.active:
                    agreement.property.has_active_service = False
                    agreement.property.stripe_subscription_id = None
                    agreement.property.save()
                    logger.info(f"✅ Property {agreement.property.id} marked as inactive (no other active agreements).")
                elif agreement.active:
                    agreement.property.has_active_service = True
                    agreement.property.stripe_subscription_id = subscription['id']
                    agreement.property.save()
                    logger.info(f"✅ Property {agreement.property.id} marked active with subscription {subscription['id']}.")

        except ServiceAgreement.DoesNotExist:
            logger.warning(f"⚠️ Webhook Warning: ServiceAgreement for subscription {subscription['id']} not found for {event['type']} event.")
            return HttpResponse(status=200)
        except Exception as e:
            logger.error(f"❌ Unexpected error in subscription {event['type']} webhook: {e}", exc_info=True)
            return HttpResponse(status=400)

    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        subscription_id = invoice.get('subscription')
        if subscription_id:
            try:
                agreement = ServiceAgreement.objects.get(stripe_subscription_id=subscription_id)
                agreement.active = True
                if invoice.get('period_end'):
                    agreement.stripe_current_period_end = timezone.datetime.fromtimestamp(
                        invoice['period_end'], tz=timezone.utc
                    ).date()
                agreement.save()
                if agreement.property:
                    agreement.property.has_active_service = True
                    agreement.property.stripe_subscription_id = subscription_id
                    agreement.property.save()
                logger.info(f"✅ Invoice payment succeeded for subscription {subscription_id}. Agreement {agreement.id} updated.")

                print("DEBUG: Attempting to send subscription confirmation email.")
                try:
                    subject = f"Your Service Subscription for {agreement.service_package.name} at {agreement.property.address_summary} is Active!"
                    html_message = render_to_string(
                        'emails/subscription_confirmation.html',
                        {
                            'user': agreement.user,
                            'package': agreement.service_package,
                            'property': agreement.property,
                            'agreement_date': timezone.now().strftime("%Y-%m-%d"),
                        }
                    )
                    print(f"DEBUG: Rendered HTML Message (first 200 chars):\n{html_message[:200]}")
                    plain_message = strip_tags(html_message)
                    print(f"DEBUG: Plain Text Message (first 200 chars):\n{plain_message[:200]}")
                    from_email = settings.DEFAULT_FROM_EMAIL
                    to_email = agreement.user.email
                    print(f"DEBUG: Email details - From: {from_email}, To: {to_email}, Subject: {subject}")

                    send_mail(
                        subject,
                        plain_message,
                        from_email,
                        [to_email],
                        html_message=html_message,
                        fail_silently=True,
                    )
                    logger.info(f"Subscription confirmation email sent to {to_email} via webhook for subscription {subscription_id}.")
                    print(f"DEBUG: send_mail call completed successfully (fail_silently=True).")
                except Exception as email_err:
                    logger.error(f"Error sending webhook-triggered subscription confirmation email to {agreement.user.email}: {email_err}", exc_info=True)
                    print(f"ERROR: Email sending failed with exception: {email_err}")

            except ServiceAgreement.DoesNotExist:
                logger.warning(f"⚠️ Invoice payment succeeded for unknown subscription {subscription_id}.")
        return HttpResponse(status=200)

    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        subscription_id = invoice.get('subscription')
        if subscription_id:
            try:
                agreement = ServiceAgreement.objects.get(stripe_subscription_id=subscription_id)
                agreement.active = False
                agreement.save()
                if agreement.property:
                    other_active_agreements = ServiceAgreement.objects.filter(
                        property=agreement.property,
                        active=True
                    ).exclude(id=agreement.id).exists()
                    if not other_active_agreements:
                        agreement.property.has_active_service = False
                        agreement.property.stripe_subscription_id = None
                        agreement.property.save()
                logger.warning(f"⚠️ Invoice payment failed for subscription {subscription_id}. Agreement {agreement.id} marked inactive.")
            except ServiceAgreement.DoesNotExist:
                logger.warning(f"⚠️ Invoice payment failed for unknown subscription {subscription_id}.")
        return HttpResponse(status=200)

    return HttpResponse(status=200)


@login_required
@user_passes_test(staff_or_superuser_required)
def all_subscriptions(request):
    """
    Displays a list of all service agreements (subscriptions) for staff/superusers.
    """
    agreements = ServiceAgreement.objects.select_related('user', 'service_package', 'property').all().order_by('-date_created')
    return render(request, 'memberships/all_subscriptions.html', {
        'agreements': agreements,
    })


@login_required
def sidebar_fragment(request):
    """
    Renders the dynamic content for the sidebar offcanvas.
    This is an AJAX endpoint.
    """
    selected_packages = request.session.get('selected_packages', {})

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

    html = render_to_string('memberships/sidebar_content.html', {
        'selected_packages': selected_packages,
        'user': request.user,
        'user_properties': user_properties,
    }, request=request)

    return JsonResponse({'success': True, 'html': html})

@login_required
@require_POST
@csrf_protect
@user_passes_test(staff_or_superuser_required)
def cancel_agreement(request, agreement_id):
    """
    Allows staff/superusers to cancel an active service agreement.
    This attempts to cancel the subscription on Stripe and then updates the local record.
    """
    agreement = get_object_or_404(ServiceAgreement, id=agreement_id, active=True)

    if not agreement.stripe_subscription_id:
        return JsonResponse({'success': False, 'error': 'This agreement does not have a Stripe subscription ID and cannot be cancelled via Stripe.'}, status=400)

    try:
        # Cancel the subscription on Stripe
        stripe_subscription = stripe.Subscription.delete(
            agreement.stripe_subscription_id,
            # You can set `at_period_end=True` if you want it to cancel at the end of the current billing period
            # For immediate cancellation:
            at_period_end=False
        )
        logger.info(f"Stripe Subscription {agreement.stripe_subscription_id} cancelled.")

        with transaction.atomic():
            # Update the local ServiceAgreement
            agreement.active = False
            agreement.end_date = timezone.now().date()
            agreement.status = 'cancelled' # Or a specific 'cancelled' status if you have one
            agreement.save()
            logger.info(f"ServiceAgreement {agreement_id} status updated to inactive.")

            # Update the associated Property's status if no other active agreements exist
            # Note: The webhook for 'customer.subscription.deleted' will also handle this,
            # but updating it here provides immediate feedback.
            other_active_agreements = ServiceAgreement.objects.filter(
                property=agreement.property,
                active=True
            ).exclude(id=agreement.id).exists()

            if not other_active_agreements:
                agreement.property.has_active_service = False
                agreement.property.stripe_subscription_id = None
                agreement.property.save()
                logger.info(f"Property {agreement.property.id} marked as inactive (no remaining active agreements).")

        # Send cancellation confirmation email
        try:
            subject = f"Your Service Agreement for {agreement.service_package.name} at {agreement.property.address_summary} has been Cancelled"
            html_message = render_to_string(
                'emails/subscription_cancellation_confirmation.html', # Make sure this template exists
                {
                    'user': agreement.user,
                    'package': agreement.service_package,
                    'property': agreement.property,
                    'agreement_date': agreement.end_date.strftime("%Y-%m-%d"),
                }
            )
            plain_message = strip_tags(html_message)
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [agreement.user.email],
                html_message=html_message,
                fail_silently=True,
            )
            logger.info(f"Cancellation confirmation email sent to {agreement.user.email} for agreement {agreement_id}.")
        except Exception as email_err:
            logger.error(f"Error sending cancellation confirmation email for agreement {agreement_id}: {email_err}", exc_info=True)


        messages.success(request, f"Service Agreement for {agreement.service_package.name} at {agreement.property.address_summary} cancelled successfully.")
        return JsonResponse({'success': True, 'message': 'Service Agreement cancelled successfully.'})

    except stripe.error.StripeError as e:
        logger.error(f"Stripe Error cancelling subscription {agreement.stripe_subscription_id}: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': f'Stripe error: {str(e)}'}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error cancelling agreement {agreement_id}: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': 'An unexpected error occurred during cancellation.'}, status=500)
