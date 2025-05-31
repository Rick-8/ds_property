import os
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

from staff_portal.services import create_subscription_job
from staff_portal.models import Job
from .models import ServiceAgreement, ServicePackage
from .forms import ServicePackageForm
from accounts.models import Property, Profile

# Email imports
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime

User = get_user_model()

logger = logging.getLogger(__name__)

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


@login_required
@user_passes_test(staff_or_superuser_required)
def package_create(request):
    """
    Creates a new ServicePackage in Django and a corresponding Product/Price in Stripe.
    """
    if request.method == 'POST':
        form = ServicePackageForm(request.POST)
        if form.is_valid():
            package = form.save(commit=False)

            display_name = f"{package.get_category_display()} {package.get_tier_display()} - {package.name}"
            price_in_cents = int(package.price_usd * 100)

            try:
                with transaction.atomic():
                    stripe_product = stripe.Product.create(
                        name=display_name,
                        description=package.description,
                        active=package.is_active,
                        metadata={
                            'category': package.category,
                            'tier': package.tier,
                        }
                    )
                    package.stripe_product_id = stripe_product.id
                    logger.info(f"Stripe Product created: {stripe_product.id} for package '{package.name}'")

                    stripe_price = stripe.Price.create(
                        product=stripe_product.id,
                        unit_amount=price_in_cents,
                        currency='usd',
                        recurring={
                            'interval': 'month',
                        },
                        active=package.is_active,
                        metadata={
                            'category': package.category,
                            'tier': package.tier,
                        }
                    )
                    package.stripe_price_id = stripe_price.id
                    logger.info(f"Stripe Price created: {stripe_price.id} for product '{stripe_product.id}'")

                    package.save()

                    stripe.Product.modify(
                        stripe_product.id,
                        metadata={'django_package_id': package.id}
                    )
                    stripe.Price.modify(
                        stripe_price.id,
                        metadata={'django_package_id': package.id}
                    )
                    logger.info(f"Stripe Product/Price metadata updated with django_package_id: {package.id}")


                    messages.success(request, f"Service package '{package.name}' created successfully and linked to Stripe.")
                    return redirect('servicepackage_list')

            except stripe.error.StripeError as e:
                logger.error(f"Stripe API Error during package creation for '{package.name}': {e}", exc_info=True)
                messages.error(request, f"Failed to create package in Stripe: {e.user_message or e}")
            except Exception as e:
                logger.error(f"Unexpected error during package creation for '{package.name}': {e}", exc_info=True)
                messages.error(request, f"An unexpected error occurred: {e}")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = ServicePackageForm()

    return render(request, 'memberships/servicepackage_form.html', {'form': form, 'title': 'Create Service Package'})

@superuser_required
def package_update(request, pk):
    package = get_object_or_404(ServicePackage, pk=pk)
    old_price = package.price_usd  # Track if price changed

    if request.method == 'POST':
        form = ServicePackageForm(request.POST, instance=package)
        if form.is_valid():
            updated_package = form.save(commit=False)
            display_name = f"{updated_package.get_category_display()} {updated_package.get_tier_display()} - {updated_package.name}"

            try:
                # Update Stripe Product
                if updated_package.stripe_product_id:
                    stripe.Product.modify(
                        updated_package.stripe_product_id,
                        name=display_name,
                        description=updated_package.description,
                        active=updated_package.is_active,
                        metadata={
                            'category': updated_package.category,
                            'tier': updated_package.tier,
                            'django_package_id': updated_package.id,
                        }
                    )

                # If price changed, create a new Stripe Price (Stripe prices are immutable)
                if updated_package.price_usd != old_price:
                    new_stripe_price = stripe.Price.create(
                        product=updated_package.stripe_product_id,
                        unit_amount=int(updated_package.price_usd * 100),
                        currency='usd',
                        recurring={'interval': 'month'},
                        active=updated_package.is_active,
                        metadata={
                            'category': updated_package.category,
                            'tier': updated_package.tier,
                            'django_package_id': updated_package.id,
                        }
                    )
                    updated_package.stripe_price_id = new_stripe_price.id

                updated_package.save()
                messages.success(request, "Service package updated successfully and Stripe updated.")
                return redirect('servicepackage_list')

            except stripe.error.StripeError as e:
                logger.error(f"Stripe error during update of '{updated_package.name}': {e}", exc_info=True)
                messages.error(request, f"Error updating Stripe: {e.user_message or str(e)}")

    else:
        form = ServicePackageForm(instance=package)

    return render(request, 'memberships/servicepackage_form.html', {'form': form, 'title': 'Update Service Package'})


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

    logger.debug(f"In confirm_contract view, settings.STRIPE_PUBLISHABLE_KEY = '{settings.STRIPE_PUBLISHABLE_KEY}'")

    return render(request, 'memberships/confirm_contract.html', context)


@login_required
@csrf_protect
@require_POST
def payment(request, package_id):
    """
    Handles processing subscription creation using Stripe's Subscription API directly.
    This view expects a POST request with 'payment_method_id' and 'property_id' in JSON body.
    Includes a final critical check for active agreements and creates/updates Django models.
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

    logger.debug(f"payment view - Received property_id from JSON: {property_id}")
    logger.debug(f"payment view - Received payment_method_id from JSON: {payment_method_id}")

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
            service_agreement_obj = ServiceAgreement.objects.create(
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

            request.session['last_subscribed_agreement_id'] = service_agreement_obj.id
            request.session['last_subscribed_package_id'] = package.id

            property_obj.is_subscribed = True
            property_obj.save()
            logger.info(f"Property {property_obj.id} status updated to is_subscribed=True.")

        if subscription.latest_invoice:
            payment_intent = subscription.latest_invoice.get('payment_intent')

            if payment_intent:
                if (payment_intent.status == 'requires_action' or
                        payment_intent.status == 'requires_confirmation'):
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
    This view also handles:
    - Activating the service agreement and property
    - Creating a job for staff portal
    - Sending confirmation email to the user
    - Sending notification emails to all superusers
    """

    user = request.user
    package = None
    agreement = None

    logger.debug(f"*** DEBUG START for user: {user.id} ({user.email}) ***")
    logger.debug(f"Session keys: {list(request.session.keys())}")

    # Retrieve package from session
    package_id = request.session.get('last_subscribed_package_id')
    if package_id:
        try:
            package = ServicePackage.objects.get(id=package_id)
            logger.debug(f"Found package: {package.name} (ID: {package.id})")
        except ServicePackage.DoesNotExist:
            logger.error(f"Package with ID {package_id} not found.")
            messages.error(request, "Subscription package details not found. Please contact support.")
    else:
        logger.warning("No package ID found in session.")
        messages.warning(request, "No subscription package information found. Please contact support.")

    # Retrieve agreement from session or fallback
    if package:
        agreement_id = request.session.get('last_subscribed_agreement_id')
        try:
            if agreement_id:
                agreement = ServiceAgreement.objects.get(id=agreement_id, user=user, service_package=package)
                logger.debug(f"Found agreement via session ID: {agreement.id}")
            else:
                # fallback: get most recent active agreement for this user/package
                agreement = ServiceAgreement.objects.filter(user=user, service_package=package, active=True).order_by('-date_created', '-id').first()
                if agreement:
                    logger.debug(f"Found agreement via fallback: {agreement.id}")
                else:
                    messages.warning(request, "Your subscription agreement could not be found. Please contact support.")
                    logger.warning(f"No active agreement found for user {user.id} and package {package.id}.")
        except ServiceAgreement.DoesNotExist:
            messages.error(request, "Subscription agreement details not found. Please contact support.")
            logger.error(f"Agreement with ID {agreement_id} not found for user {user.id}.")
        except Exception as e:
            messages.error(request, "Error retrieving subscription details. Please contact support.")
            logger.error(f"Error fetching agreement for user {user.id}: {e}", exc_info=True)
    else:
        logger.warning("Skipping agreement retrieval because package not found.")

    # Activate agreement and property if not already active
    if agreement and package:
        try:
            if not agreement.active:
                agreement.active = True
                if not agreement.start_date:
                    agreement.start_date = datetime.now().date()
                agreement.save()
                logger.info(f"Activated agreement {agreement.id}")

            if hasattr(agreement, 'property') and agreement.property:
                if not agreement.property.is_active:
                    agreement.property.is_active = True
                    agreement.property.has_active_service = True
                    agreement.property.save()
                    logger.info(f"Activated property {agreement.property.id}")

        except Exception as e:
            messages.error(request, "Failed to activate subscription details. Please contact support.")
            logger.error(f"Error activating agreement or property for agreement {agreement.id}: {e}", exc_info=True)

        # ✅ Refactored job creation
        try:
            job = create_subscription_job(agreement, package)
            logger.info(f"Created Job {job.id} for subscription agreement {agreement.id}")
        except Exception as e:
            messages.error(request, "Failed to create job for subscription. Please contact support.")
            logger.error(f"Job creation failed for agreement {agreement.id}: {e}", exc_info=True)

        # Prepare data for emails
        dashboard_url = request.build_absolute_uri(reverse('account_dashboard'))

        # Send confirmation email to the user
        try:
            subject = f"Subscription Confirmation - {package.name}"
            html_content = render_to_string('emails/package_confirmation_email.html', {
                'user': user,
                'package': package,
                'agreement': agreement,
                'dashboard_url': dashboard_url,
            })
            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(subject, text_content, 'noreply@dsproperty.com', [user.email])
            email.attach_alternative(html_content, "text/html")
            email.send()
            logger.info(f"Sent subscription confirmation email to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send confirmation email to {user.email}: {e}", exc_info=True)

        # Notify all superusers
        try:
            superusers = User.objects.filter(is_superuser=True).values_list('email', flat=True)
            if superusers:
                subject = f"New Subscription: {user.get_full_name()} - {package.name}"
                admin_html_content = render_to_string('emails/office_notification_email.html', {
                    'user': user,
                    'package': package,
                    'agreement': agreement,
                })
                admin_text_content = strip_tags(admin_html_content)

                admin_email = EmailMultiAlternatives(subject, admin_text_content, 'noreply@dsproperty.com', list(superusers))
                admin_email.attach_alternative(admin_html_content, "text/html")
                admin_email.send()
                logger.info("Sent notification emails to superusers.")
        except Exception as e:
            logger.error(f"Failed to send notification emails to superusers: {e}", exc_info=True)

    # Clean session variables related to subscription
    for key in ['last_subscribed_package_id', 'last_subscribed_agreement_id']:
        if key in request.session:
            del request.session[key]
    request.session.modified = True

    # Prepare display data for template
    subscription_start_date_display = agreement.start_date.strftime("%B %d, %Y") if agreement and agreement.start_date else datetime.now().strftime("%B %d, %Y")
    amount_paid_display = f"{agreement.amount_paid:.2f}" if agreement and agreement.amount_paid else "0.00"

    context = {
        'package': package,
        'agreement': agreement,
        'amount_paid_display': amount_paid_display,
        'subscription_start_date_display': subscription_start_date_display,
    }

    return render(request, 'memberships/subscription_success.html', context)


@login_required
def resend_confirmation_email(request, agreement_id):
    """
    Allows a user to resend their subscription confirmation email for a specific agreement.
    """
    user = request.user
    agreement = get_object_or_404(ServiceAgreement, id=agreement_id, user=user)
    package = agreement.service_package

    subscription_start_date_display = (agreement.start_date.strftime("%B %d, %Y")
                                       if agreement.start_date else
                                       datetime.now().strftime("%B %d, %Y"))
    amount_paid_display = (f"{agreement.amount_paid:.2f}"
                           if agreement.amount_paid is not None else "0.00")

    dashboard_url = request.build_absolute_uri(reverse('account_dashboard'))

    email_context = {
        'user': user,
        'package': package,
        'agreement': agreement,
        'site_name': 'DS Property Management',
        'dashboard_url': dashboard_url,
        'subscription_start_date_display': subscription_start_date_display,
        'amount_paid_display': amount_paid_display,
        'whatsapp_number': '+447911123456',
        'office_phone_number': '+441234567890',
    }

    if user.email:
        try:
            html_message = render_to_string('emails/package_confirmation_email.html', email_context)
            plain_message = strip_tags(html_message)

            pdf_file_name = 'dsp-terms-conditions.pdf'
            pdf_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', pdf_file_name)

            pdf_attachment = None
            if not os.path.exists(pdf_path):
                logger.error(f"PDF file not found at: {pdf_path}. Cannot attach terms and conditions.")
            else:
                with open(pdf_path, 'rb') as pdf_file:
                    pdf_data = pdf_file.read()
                pdf_attachment = (pdf_file_name, pdf_data, 'application/pdf')

            user_email = EmailMultiAlternatives(
                subject=f"Welcome to {email_context['site_name']}! Your Subscription is Confirmed - Terms Included",
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            user_email.attach_alternative(html_message, "text/html")

            if pdf_attachment:
                user_email.attach(*pdf_attachment)

            user_email.send(fail_silently=False)
            messages.success(request, "Confirmation email resent successfully!")
            logger.info(f"Subscription confirmation email (with PDF) resent to {user.email} for agreement {agreement.id}.")

        except Exception as e:
            logger.error(f"Failed to resend subscription confirmation email to {user.email}: {e}", exc_info=True)
            messages.error(request, "Failed to resend confirmation email. Please contact support.")
    else:
        messages.warning(request, "Cannot resend email: No email address associated with your account.")

    return redirect('account_dashboard')


@login_required
def subscription_cancel(request):
    """
    Page displayed if subscription process is cancelled (e.g., user navigates away).
    """
    messages.info(request, "Your subscription setup was cancelled.")
    return render(request, 'memberships/subscription_cancel.html')


@login_required
@require_POST
def cancel_agreement(request, agreement_id):
    """
    Allows a user to cancel an active service agreement.
    This should also trigger cancellation on Stripe and send a confirmation email.
    """
    agreement = get_object_or_404(ServiceAgreement, id=agreement_id, user=request.user, active=True)
    user = request.user

    try:
        with transaction.atomic():
            if agreement.stripe_subscription_id:
                stripe.Subscription.delete(agreement.stripe_subscription_id)
                logger.info(f"Stripe subscription {agreement.stripe_subscription_id} cancelled for agreement {agreement.id}.")
            else:
                logger.warning(f"Agreement {agreement.id} has no Stripe subscription ID. Proceeding with local cancellation only.")

            agreement.active = False
            agreement.end_date = timezone.now().date()
            agreement.status = 'cancelled'
            agreement.save()
            logger.info(f"ServiceAgreement {agreement.id} marked as cancelled in Django.")

            if agreement.property:
                other_active_agreements_for_property = ServiceAgreement.objects.filter(
                    property=agreement.property,
                    active=True
                ).exclude(id=agreement.id).exists()

                if not other_active_agreements_for_property:
                    agreement.property.has_active_service = False
                    agreement.property.stripe_subscription_id = None
                    agreement.property.save()
                    logger.info(f"Property {agreement.property.id} status updated to has_active_service=False as no other active agreements.")
                else:
                    logger.info(f"Property {agreement.property.id} still has other active agreements.")

            messages.success(request, f"Your '{agreement.service_package.name}' service for {agreement.property.address_summary} has been successfully cancelled.")

            if user.email:
                try:
                    cancellation_date_display = timezone.now().strftime("%B %d, %Y")
                    dashboard_url = request.build_absolute_uri(reverse('account_dashboard'))

                    email_context = {
                        'user': user,
                        'agreement': agreement,
                        'service_package_name': agreement.service_package.name,
                        'property_address': agreement.property.address_summary,
                        'cancellation_date_display': cancellation_date_display,
                        'site_name': 'DS Property Management',
                        'dashboard_url': dashboard_url,
                        'contact_email': settings.DEFAULT_FROM_EMAIL,
                    }

                    html_message = render_to_string('emails/subscription_cancellation_confirmation.html', email_context)
                    plain_message = strip_tags(html_message)

                    cancellation_email = EmailMultiAlternatives(
                        subject=f"Confirmation: Your {agreement.service_package.name} Service for {agreement.property.address_summary} Has Been Cancelled",
                        body=plain_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[user.email],
                    )
                    cancellation_email.attach_alternative(html_message, "text/html")
                    cancellation_email.send(fail_silently=False)
                    logger.info(f"Cancellation confirmation email sent to {user.email} for agreement {agreement.id}.")
                except Exception as e:
                    logger.error(f"Failed to send cancellation confirmation email to {user.email}: {e}", exc_info=True)
                    messages.warning(request, "Failed to send cancellation confirmation email. Please contact support.")
            else:
                logger.warning(f"Agreement {agreement.id} cancelled but no email address for user {user.id} to send confirmation.")
                messages.warning(request, "Your service was cancelled, but we couldn't send an email confirmation (no email address on file).")

            return JsonResponse({'success': True, 'redirect_url': reverse('account_dashboard')})

    except stripe.error.StripeError as e:
        logger.error(f"Stripe API Error during subscription cancellation for agreement {agreement.id}: {e}", exc_info=True)
        messages.error(request, f"Failed to cancel subscription with Stripe: {e}. Please try again or contact support.")
        return JsonResponse({"success": False, "error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error during subscription cancellation for agreement {agreement.id}: {e}", exc_info=True)
        messages.error(request, "An unexpected error occurred during cancellation. Please contact support.")
        return JsonResponse({"success": False, "error": "An unexpected error occurred."}, status=500)


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
        package_id = metadata.get('package_id')

        if not all([user_id, property_id, package_id, subscription['id']]):
            logger.warning(f"⚠️ Missing required metadata in customer.subscription.created: user_id({user_id}), property_id({property_id}), package_id({package_id}), subscription_id({subscription['id']}).")
            return HttpResponse(status=400)

        try:
            user = User.objects.get(id=user_id)
            prop = Property.objects.get(id=property_id)
            service_package = ServicePackage.objects.get(id=package_id)

            ServiceAgreement.objects.filter(property=prop, active=True).update(active=False, end_date=timezone.now().date())
            logger.info(f"ℹ️ Deactivated previous active agreements for property {prop.id}.")

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

            if subscription['status'] == 'canceled':
                agreement.active = False
                agreement.end_date = timezone.now().date()
                agreement.status = 'cancelled'
                logger.info(f"ℹ️ ServiceAgreement {agreement.id} marked as inactive due to cancellation.")
            elif subscription['status'] == 'active':
                agreement.active = True
                agreement.status = 'active'
                agreement.stripe_current_period_end = timezone.datetime.fromtimestamp(
                    subscription['current_period_end'], tz=timezone.utc
                ).date() if 'current_period_end' in subscription else None
                logger.info(f"ℹ️ ServiceAgreement {agreement.id} updatd to active.")
            else:
                logger.warning(f"⚠️ Unhandled subscription status '{subscription['status']}' for agreement {agreement.id}. Marking as inactive.")
                agreement.active = False
                agreement.status = subscription['status']
                agreement.end_date = timezone.now().date()

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
                agreement.status = 'active'
                agreement.amount_paid_last_invoice = invoice.get('amount_paid') / 100.0
                agreement.last_payment_date = timezone.datetime.fromtimestamp(
                    invoice['created'], tz=timezone.utc
                ).date()

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
                    plain_message = strip_tags(html_message)
                    from_email = settings.DEFAULT_FROM_EMAIL
                    to_email = agreement.user.email

                    email = EmailMessage(
                        subject,
                        plain_message,
                        from_email,
                        [to_email],
                    )
                    email.attach_alternative(html_message, "text/html")

                    pdf_file_name = 'dsp-terms-conditions.pdf'
                    pdf_path = os.path.join(settings.BASE_DIR, 'static', 'pdfs', pdf_file_name)
                    if os.path.exists(pdf_path):
                        with open(pdf_path, 'rb') as pdf_file:
                            pdf_data = pdf_file.read()
                        email.attach(pdf_file_name, pdf_data, 'application/pdf')
                    else:
                        logger.error(f"PDF file not found at: {pdf_path}. Cannot attach terms and conditions to webhook email.")

                    email.send(fail_silently=True)
                    logger.info(f"Subscription confirmation email sent to {to_email} via webhook for subscription {subscription_id}.")
                except Exception as email_err:
                    logger.error(f"Error sending webhook-triggered subscription confirmation email to {agreement.user.email}: {email_err}", exc_info=True)


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
                agreement.status = 'past_due'
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
                logger.warning(f"⚠️ Invoice payment failed for subscription {subscription_id}. Agreement {agreement.id} marked inactive/past_due.")

                user_to_notify = agreement.user
                if user_to_notify and user_to_notify.email:
                    try:
                        subject = "Important: Your Subscription Payment Failed"
                        html_message = render_to_string(
                            'emails/payment_failed_notification.html',
                            {
                                'user': user_to_notify,
                                'agreement': agreement,
                                'site_name': 'DS Property Management',
                                'dashboard_url': request.build_absolute_uri(reverse('account_dashboard')),
                                'customer_portal_url': 'YOUR_STRIPE_CUSTOMER_PORTAL_URL_HERE',
                            }
                        )
                        plain_message = strip_tags(html_message)
                        from_email = settings.DEFAULT_FROM_EMAIL
                        to_email = user_to_notify.email

                        email = EmailMessage(
                            subject,
                            plain_message,
                            from_email,
                            [to_email],
                        )
                        email.attach_alternative(html_message, "text/html")
                        email.send(fail_silently=True)
                        logger.info(f"Payment failed notification email sent to {to_email}.")
                    except Exception as email_err:
                        logger.error(f"Error sending payment failure email to {user_to_notify.email}: {email_err}", exc_info=True)

            except ServiceAgreement.DoesNotExist:
                logger.warning(f"⚠️ Invoice payment failed for unknown subscription {subscription_id}.")
        return HttpResponse(status=200)

    else:
        logger.info(f"🤷‍♀️ Webhook: Unhandled event type {event['type']}")

    return HttpResponse(status=200)


@login_required
@user_passes_test(staff_or_superuser_required)
def all_subscriptions(request):
    """
    Displays a list of all active service agreements (subscriptions) for staff/superusers.
    """
    agreements = ServiceAgreement.objects.select_related('user', 'service_package', 'property')\
                .filter(active=True)\
                .order_by('-date_created')
    return render(request, 'memberships/all_subscriptions.html', {
        'agreements': agreements,
    })


@login_required
def sidebar_fragment(request):
    """
    Renders a fragment for the sidebar, likely showing current subscriptions or property status.
    This view should probably be included in a template via Django's include tag or similar.
    """
    user_properties = Property.objects.filter(profile__user=request.user, is_active=True).prefetch_related(
        Prefetch(
            'serviceagreement_set',
            queryset=ServiceAgreement.objects.filter(active=True).select_related('service_package'),
            to_attr='active_agreements'
        )
    )

    for prop in user_properties:
        prop.has_active_agreement = bool(prop.active_agreements)
        if prop.has_active_agreement:
            prop.current_package = prop.active_agreements[0].service_package
        else:
            prop.current_package = None

    context = {
        'user_properties': user_properties,
    }
    return render(request, 'memberships/sidebar_content.html', context)
