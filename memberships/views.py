from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.contrib.auth.decorators import user_passes_test, login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_protect

from .models import ServicePackage
from .forms import ServicePackageForm
from accounts.models import Property
from django.urls import reverse
from django.contrib import messages

import stripe
import json
import logging
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)


def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


def servicepackage_list(request):
    packages = ServicePackage.objects.all()
    category = "Silver"
    return render(request, "memberships/list.html", {
        "packages": packages,
        "category": category,
    })


@superuser_required
def package_create(request):
    if request.method == 'POST':
        form = ServicePackageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('servicepackage_list')
    else:
        form = ServicePackageForm()
    return render(request, 'memberships/form.html', {'form': form, 'title': 'Create Service Package'})


@superuser_required
def package_update(request, pk):
    package = get_object_or_404(ServicePackage, pk=pk)
    if request.method == 'POST':
        form = ServicePackageForm(request.POST, instance=package)
        if form.is_valid():
            form.save()
            return redirect('servicepackage_list')
    else:
        form = ServicePackageForm(instance=package)
    return render(request, 'memberships/form.html', {'form': form, 'title': 'Update Service Package'})


@superuser_required
def package_delete(request, pk):
    package = get_object_or_404(ServicePackage, pk=pk)
    if request.method == 'POST':
        package.delete()
        return redirect('servicepackage_list')
    return render(request, 'memberships/confirm_delete.html', {'package': package})


@login_required
def package_selection(request):
    packages = ServicePackage.objects.filter(is_active=True)
    properties = Property.objects.filter(profile__user=request.user, is_active=True)
    return render(request, 'memberships/package_selection.html', {
        'packages': packages,
        'properties': properties,
    })


@login_required
def select_package(request, package_id):
    if request.method == 'POST':
        package = get_object_or_404(ServicePackage, id=package_id, is_active=True)
        property_id = request.POST.get('property_id')
        selected_packages = request.session.get('selected_packages', {})

        property_obj = None
        if property_id:
            try:
                property_obj = Property.objects.get(id=property_id, profile__user=request.user, is_active=True)
            except Property.DoesNotExist:
                property_obj = None

        selected_packages[package.category] = {
            'id': package.id,
            'name': package.name,
            'category': package.get_category_display(),
            'tier': package.get_tier_display(),
            'price_usd': float(package.price_usd),
            'property_id': property_obj.id if property_obj else None,
            'property_label': property_obj.label if property_obj else '',
            'property_address_summary': property_obj.address_summary if property_obj else '',
        }

        request.session['selected_packages'] = selected_packages
        request.session.modified = True

        return JsonResponse({'success': True, 'package': selected_packages[package.category]})

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


@login_required
def confirm_contract(request, package_id):
    package = get_object_or_404(ServicePackage, pk=package_id)
    property_id = request.GET.get('property_id')
    property_obj = None
    if property_id:
        property_obj = get_object_or_404(Property, pk=property_id)
    context = {
        'package': package,
        'property': property_obj,
    }
    return render(request, 'memberships/confirm_contract.html', context)


@require_POST
@login_required
def remove_package(request, package_id):
    selected_packages = request.session.get('selected_packages', {})
    to_remove_key = None
    for key, pkg in selected_packages.items():
        if str(pkg['id']) == str(package_id):
            to_remove_key = key
            break

    if to_remove_key:
        del selected_packages[to_remove_key]
        request.session['selected_packages'] = selected_packages
        request.session.modified = True
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Package not found'}, status=404)


@login_required
@require_POST
def update_package_property(request, package_id):
    try:
        data = json.loads(request.body)
        property_id = data.get('property_id')
        selected_packages = request.session.get('selected_packages', {})

        category_key = None
        for category, pkg in selected_packages.items():
            if str(pkg['id']) == str(package_id):
                category_key = category
                break

        if not category_key:
            return JsonResponse({'success': False, 'error': 'Package not found in session'}, status=400)

        if not property_id:
            return JsonResponse({'success': False, 'error': 'No property_id provided'}, status=400)

        try:
            property_id_int = int(property_id)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid property_id'}, status=400)

        try:
            property_obj = Property.objects.get(
                id=property_id_int,
                profile__user=request.user,
                is_active=True
            )
        except Property.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid property selected'}, status=400)

        selected_packages[category_key]['property_id'] = property_obj.id
        selected_packages[category_key]['property_label'] = property_obj.label
        selected_packages[category_key]['property_address_summary'] = property_obj.address_summary

        request.session['selected_packages'] = selected_packages
        request.session.modified = True

        return JsonResponse({
            'success': True,
            'package': selected_packages[category_key],
            'property_id': property_obj.id,
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)


logger = logging.getLogger(__name__)


@login_required
@require_POST
def create_checkout_session(request):
    try:
        selected_packages = request.session.get('selected_packages', {})

        if not selected_packages:
            return JsonResponse({'error': 'No package selected'}, status=400)

        # Take the first selected package
        first_pkg = next(iter(selected_packages.values()))

        package_obj = ServicePackage.objects.get(id=first_pkg['id'])
        price_id = package_obj.stripe_price_id

        property_id = first_pkg.get('property_id')
        if not property_id:
            return JsonResponse({'error': 'No property selected'}, status=400)

        # Validate property belongs to user and is active
        from accounts.models import Property
        try:
            property_obj = Property.objects.get(id=property_id, profile__user=request.user, is_active=True)
        except Property.DoesNotExist:
            return JsonResponse({'error': 'Invalid property selected'}, status=400)

        # Create Stripe Checkout session with metadata passed via subscription_data
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='subscription',
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            customer_email=request.user.email,
            subscription_data={
                'metadata': {
                    'property_id': str(property_obj.id),
                    'package_name': package_obj.name,
                }
            },
            success_url=request.build_absolute_uri(reverse('payment_success')),
            cancel_url=request.build_absolute_uri(reverse('package_selection')),
        )

        return JsonResponse({'sessionId': checkout_session.id})

    except Exception as e:
        logger.error(f"Stripe Checkout Session creation failed: {e}")
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@csrf_protect
def payment(request, package_id):
    package = get_object_or_404(ServicePackage, pk=package_id)

    # Ensure package has a Stripe price ID configured
    if not package.stripe_price_id:
        messages.error(request, "Sorry, this package is not configured properly for payment. Please contact support.")
        return redirect("package_selection")

    property_id = request.GET.get("property_id")
    property_obj = None
    if property_id:
        property_obj = get_object_or_404(Property, pk=property_id)

    if request.method == "POST":
        payment_method_id = request.POST.get("payment_method_id")
        if not payment_method_id:
            return JsonResponse({"error": "Missing payment_method_id"}, status=400)

        try:
            # Retrieve or create Stripe customer
            if not hasattr(request.user, "stripe_customer_id") or not request.user.stripe_customer_id:
                customer = stripe.Customer.create(email=request.user.email)
                request.user.stripe_customer_id = customer.id
                request.user.save()
            else:
                customer = stripe.Customer.retrieve(request.user.stripe_customer_id)

            # Attach and set default payment method
            stripe.PaymentMethod.attach(payment_method_id, customer=customer.id)
            stripe.Customer.modify(
                customer.id,
                invoice_settings={"default_payment_method": payment_method_id},
            )

            # Create subscription
            stripe.Subscription.create(
                customer=customer.id,
                items=[{'price': package.stripe_price_id}],
                default_payment_method=payment_method_id,
            )

            # (Optional) Save subscription info to DB
            messages.success(request, "Subscription successful! Thank you.")
            return redirect("subscription_success")

        except stripe.error.CardError as e:
            return JsonResponse({"error": e.user_message}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    context = {
        "package": package,
        "property": property_obj,
        "stripe_publishable_key": settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, "memberships/payment.html", context)


@login_required
def sidebar_fragment(request):
    selected_packages = request.session.get('selected_packages', {})

    html = render_to_string('memberships/partials/sidebar_content.html', {
        'selected_packages': selected_packages,
        'user': request.user,
    }, request=request)

    return JsonResponse({'success': True, 'html': html})


@login_required
def subscription_success(request):
    return render(request, 'memberships/subscription_success.html')


logger = logging.getLogger(__name__)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        logger.info(f"🔔 Received event: {event['type']}")
    except ValueError as e:
        logger.error(f"⚠️ Invalid payload: {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"⚠️ Invalid signature: {e}")
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        logger.info("✅ Webhook session data:")
        logger.info(json.dumps(session, indent=2))

        try:
            if session['mode'] == 'subscription':
                subscription_id = session.get('subscription')
                if subscription_id:
                    subscription = stripe.Subscription.retrieve(subscription_id)
                    metadata = subscription.get('metadata', {})

                    property_id = metadata.get('property_id')
                    package_name = metadata.get('package_name')

                    if not property_id or not package_name:
                        logger.warning("⚠️ Metadata missing in subscription object.")
                    else:
                        logger.info(f"✅ Metadata received: property_id={property_id}, package_name={package_name}")

                        # Perform your DB update here
                        from accounts.models import Property
                        prop = Property.objects.get(id=property_id)
                        prop.has_active_service = True
                        prop.stripe_subscription_id = subscription_id
                        prop.save()

                        logger.info(f"✅ Property {property_id} marked as active service.")
                else:
                    logger.warning("⚠️ No subscription ID found in session.")
            else:
                logger.warning("⚠️ Session is not a subscription.")
        except Property.DoesNotExist:
            logger.warning(f"⚠️ Property with ID {property_id} not found.")
            return HttpResponse(status=400)
        except Exception as e:
            logger.error(f"❌ Error processing webhook: {e}")
            return HttpResponse(status=400)

    else:
        logger.info(f"ℹ️ Unhandled event type: {event['type']}")

    return HttpResponse(status=200)
