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
from accounts.models import Property, User
from memberships.models import ServiceAgreement, ServicePackage
from staff_portal.services import create_subscription_job
from staff_portal.models import Job
from .models import ServiceAgreement, ServicePackage
from .forms import ServicePackageForm
from accounts.models import Property, Profile
from django.core.mail import EmailMessage, EmailMultiAlternatives
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
    Returns True if user is staff or superuser, else False.
    """
    return user.is_staff or user.is_superuser


def servicepackage_list(request):
    """
    Lists all service packages.
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
    Creates a new ServicePackage in Django and a Stripe Product/Price.
    """
    if request.method == 'POST':
        form = ServicePackageForm(request.POST)
        if form.is_valid():
            package = form.save(commit=False)
            display_name = (
                f"{package.get_category_display()} "
                f"{package.get_tier_display()} - {package.name}"
            )
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
                    logger.info(
                        f"Stripe Product created: {stripe_product.id} "
                        f"for package '{package.name}'"
                    )
                    stripe_price = stripe.Price.create(
                        product=stripe_product.id,
                        unit_amount=price_in_cents,
                        currency='usd',
                        recurring={'interval': 'month'},
                        active=package.is_active,
                        metadata={
                            'category': package.category,
                            'tier': package.tier,
                        }
                    )
                    package.stripe_price_id = stripe_price.id
                    logger.info(
                        f"Stripe Price created: {stripe_price.id} for product "
                        f"'{stripe_product.id}'"
                    )
                    package.save()
                    stripe.Product.modify(
                        stripe_product.id,
                        metadata={'django_package_id': package.id}
                    )
                    stripe.Price.modify(
                        stripe_price.id,
                        metadata={'django_package_id': package.id}
                    )
                    logger.info(
                        f"Stripe Product/Price metadata updated with "
                        f"django_package_id: {package.id}"
                    )
                    messages.success(
                        request,
                        f"Service package '{package.name}' created successfully "
                        f"and linked to Stripe."
                    )
                    return redirect('servicepackage_list')
            except stripe.error.StripeError as e:
                logger.error(
                    f"Stripe API Error during package creation for '{package.name}': "
                    f"{e}", exc_info=True
                )
                messages.error(
                    request,
                    f"Failed to create package in Stripe: {e.user_message or e}"
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error during package creation for '{package.name}': "
                    f"{e}", exc_info=True
                )
                messages.error(request, f"An unexpected error occurred: {e}")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = ServicePackageForm()
    return render(
        request, 'memberships/servicepackage_form.html',
        {'form': form, 'title': 'Create Service Package'}
    )


@superuser_required
def package_update(request, pk):
    """
    Updates a service package and Stripe product/price if needed.
    """
    package = get_object_or_404(ServicePackage, pk=pk)
    old_price = package.price_usd
    if request.method == 'POST':
        form = ServicePackageForm(request.POST, instance=package)
        if form.is_valid():
            updated_package = form.save(commit=False)
            display_name = (
                f"{updated_package.get_category_display()} "
                f"{updated_package.get_tier_display()} - "
                f"{updated_package.name}"
            )
            try:
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
                messages.success(
                    request,
                    "Service package updated successfully and Stripe updated."
                )
                return redirect('servicepackage_list')
            except stripe.error.StripeError as e:
                logger.error(
                    f"Stripe error during update of '{updated_package.name}': {e}",
                    exc_info=True
                )
                messages.error(
                    request,
                    f"Error updating Stripe: {e.user_message or str(e)}"
                )
    else:
        form = ServicePackageForm(instance=package)
    return render(
        request, 'memberships/servicepackage_form.html',
        {'form': form, 'title': 'Update Service Package'}
    )


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
    return render(
        request, 'memberships/confirm_delete.html', {'package': package}
    )


@login_required
def package_selection(request):
    """
    Displays available service packages for user selection, along with their
    properties. Prefetches active agreements for properties to show status.
    """
    packages = ServicePackage.objects.filter(is_active=True).order_by(
        'price_usd'
    )
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
            prop.current_package_name = (
                prop.active_agreements[0].service_package.name
            )
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
    Server-side validation to prevent selecting a property with an active
    agreement.
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
            selected_property = Property.objects.get(
                id=property_id, profile__user=request.user, is_active=True
            )
            if ServiceAgreement.objects.filter(
                property=selected_property, active=True
            ).exists():
                return JsonResponse(
                    {
                        'success': False,
                        'error': 'This property already has an active service '
                                 'agreement. Please choose another property or '
                                 'cancel the existing service.'
                    }, status=400
                )
            package_data['property_id'] = selected_property.id
            package_data['property_label'] = selected_property.label
            package_data['property_address_summary'] = (
                selected_property.address_summary
            )
        except Property.DoesNotExist:
            return JsonResponse(
                {
                    'success': False,
                    'error': 'Selected property is invalid or does not belong '
                             'to you.'
                }, status=400
            )
    selected_packages[package.category] = package_data
    request.session['selected_packages'] = selected_packages
    request.session.modified = True
    messages.success(
        request, f"'{package.name}' added to your selection."
    )
    return JsonResponse({'success': True, 'package': package_data})


@login_required
@require_POST
def update_package_property(request, package_id):
    """
    Updates the property associated with a package in the session's
    'selected_packages'. Server-side validation for property conflicts.
    """
    try:
        data = json.loads(request.body)
        property_id = data.get('property_id')
    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'error': 'Invalid JSON request.'}, status=400
        )
    selected_packages = request.session.get('selected_packages', {})
    category_key = None
    for category, pkg_data in selected_packages.items():
        if str(pkg_data.get('id')) == str(package_id):
            category_key = category
            break
    if not category_key:
        return JsonResponse(
            {'success': False, 'error': 'Package not found in session.'},
            status=404
        )
    service_package_obj = get_object_or_404(ServicePackage, pk=package_id)
    if property_id:
        try:
            selected_property = Property.objects.get(
                id=property_id, profile__user=request.user, is_active=True
            )
            existing_active_agreements = ServiceAgreement.objects.filter(
                property=selected_property, active=True
            )
            if existing_active_agreements.exists():
                is_current_package_agreement = False
                for agreement in existing_active_agreements:
                    if agreement.service_package == service_package_obj:
                        is_current_package_agreement = True
                        break
                if not is_current_package_agreement:
                    conflict_package_name = (
                        existing_active_agreements.first().service_package.name
                    )
                    return JsonResponse(
                        {
                            'success': False,
                            'error': f'This property already has an active '
                                     f'service agreement with '
                                     f'{conflict_package_name}. Please choose '
                                     f'another property or cancel the existing '
                                     f'service.'
                        }, status=400
                    )
            selected_packages[category_key]['property_id'] = selected_property.id
            selected_packages[category_key]['property_label'] = (
                selected_property.label
            )
            selected_packages[category_key]['property_address_summary'] = (
                selected_property.address_summary
            )
            messages.success(
                request,
                f"Package {selected_packages[category_key]['name']} now "
                f"associated with {selected_property.label}."
            )
        except Property.DoesNotExist:
            return JsonResponse(
                {
                    'success': False,
                    'error': 'Selected property is invalid or does not '
                             'belong to you.'
                }, status=400
            )
    else:
        selected_packages[category_key]['property_id'] = None
        selected_packages[category_key]['property_label'] = None
        selected_packages[category_key]['property_address_summary'] = None
        messages.info(
            request, "Property association removed for selected package."
        )
    request.session['selected_packages'] = selected_packages
    request.session.modified = True
    return JsonResponse(
        {'success': True, 'package': selected_packages[category_key]}
    )


@login_required
def confirm_contract(request, package_id):
    """
    Displays contract details before payment for a selected package.
    Re-validates for property conflicts.
    """
    package = get_object_or_404(ServicePackage, pk=package_id)
    property_id = request.GET.get('property_id')
    property_obj = None
    if property_id:
        property_obj = get_object_or_404(
            Property, pk=property_id, profile__user=request.user
        )
        if ServiceAgreement.objects.filter(
            property=property_obj, active=True
        ).exclude(service_package=package).exists():
            messages.error(
                request,
                "This property already has an active service agreement with a "
                "different package. Please choose another property or cancel "
                "the existing service."
            )
            return redirect(reverse('package_selection'))
    selected_packages = request.session.get('selected_packages', {})
    context = {
        'package': package,
        'property': property_obj,
        'selected_packages': selected_packages,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    }
    logger.debug(
        f"In confirm_contract view, settings.STRIPE_PUBLISHABLE_KEY = "
        f"'{settings.STRIPE_PUBLISHABLE_KEY}'"
    )
    return render(request, 'memberships/confirm_contract.html', context)


@login_required
@csrf_protect
@require_POST
def payment(request, package_id):
    """
    Handles Stripe payment for selected package/property and saves agreement.
    """
    package = get_object_or_404(ServicePackage, pk=package_id)
    if not package.stripe_price_id:
        messages.error(
            request,
            "Sorry, this package is not configured properly for payment. "
            "Please contact support."
        )
        return JsonResponse(
            {"error": "Package not configured for Stripe."}, status=400
        )
    try:
        data = json.loads(request.body)
        payment_method_id = data.get('payment_method_id')
        property_id = data.get('property_id')
    except json.JSONDecodeError:
        logger.error("Invalid JSON in payment request body.", exc_info=True)
        return JsonResponse({"error": "Invalid request format."}, status=400)
    if not property_id:
        return JsonResponse(
            {"error": "No property selected for this service package."},
            status=400
        )
    try:
        property_obj = Property.objects.get(
            pk=property_id, profile__user=request.user, is_active=True
        )
    except Property.DoesNotExist:
        return JsonResponse({"error": "Invalid property selected."}, status=400)
    existing_agreement = ServiceAgreement.objects.filter(
        property=property_obj,
        active=True
    ).first()
    if existing_agreement:
        if existing_agreement.service_package == package:
            messages.info(
                request,
                f"This property already has an active '{package.name}' "
                f"service agreement."
            )
            return JsonResponse({'success_url': reverse("subscription_success")})
        else:
            return JsonResponse(
                {
                    "error": "This property already has an active service "
                             "agreement with a different package."
                }, status=400
            )
    if not payment_method_id:
        return JsonResponse({"error": "Missing payment_method_id"}, status=400)
    try:
        if (not hasattr(request.user, "profile")
                or not request.user.profile.stripe_customer_id):
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
        else:
            customer = stripe.Customer.retrieve(
                request.user.profile.stripe_customer_id
            )
        stripe.PaymentMethod.attach(payment_method_id, customer=customer.id)
        stripe.Customer.modify(
            customer.id,
            invoice_settings={"default_payment_method": payment_method_id},
        )
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
        payment_intent = None
        latest_invoice = subscription.latest_invoice
        if latest_invoice and hasattr(latest_invoice, 'payment_intent'):
            payment_intent = latest_invoice.payment_intent
            if isinstance(payment_intent, str):
                payment_intent = stripe.PaymentIntent.retrieve(payment_intent)
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
            request.session['last_subscribed_agreement_id'] = (
                service_agreement_obj.id
            )
            request.session['last_subscribed_package_id'] = package.id
            property_obj.is_subscribed = True
            property_obj.has_active_service = True
            property_obj.save()
        if payment_intent:
            if payment_intent.status in [
                    'requires_action', 'requires_confirmation']:
                return JsonResponse({
                    'requires_action': True,
                    'payment_intent_client_secret': (
                        payment_intent.client_secret
                    ),
                    'success_url': reverse("subscription_success")
                })
            elif payment_intent.status == 'succeeded':
                messages.success(
                    request,
                    "Subscription successful! Your service is active."
                )
                request.session.pop('selected_packages', None)
                return JsonResponse(
                    {'success_url': reverse("subscription_success")}
                )
            else:
                return JsonResponse(
                    {
                        "error": (
                            f"Payment status: {payment_intent.status}. "
                            "Please contact support."
                        )
                    }, status=400
                )
        else:
            messages.success(
                request,
                "Subscription started! We'll notify you when the first "
                "payment is due."
            )
            request.session.pop('selected_packages', None)
            return JsonResponse(
                {'success_url': reverse("subscription_success")}
            )
    except stripe.error.CardError as e:
        return JsonResponse({"error": e.user_message}, status=400)
    except stripe.error.StripeError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(
            f"Unexpected error in payment view: {str(e)}", exc_info=True
        )
        return JsonResponse(
            {
                "error": "An unexpected error occurred during payment processing."
            }, status=500
        )


@login_required
def subscription_success(request):
    """
    Shows the subscription success page after payment.
    Sends confirmation and admin notification emails.
    """
    user = request.user
    package = None
    agreement = None
    package_id = request.session.pop('last_subscribed_package_id', None)
    agreement_id = request.session.pop('last_subscribed_agreement_id', None)
    request.session.modified = True
    if package_id:
        try:
            package = ServicePackage.objects.get(id=package_id)
        except ServicePackage.DoesNotExist:
            messages.error(
                request,
                "Subscription package details not found. Please contact support."
            )
            return redirect("package_selection")
    if package:
        try:
            if agreement_id:
                agreement = ServiceAgreement.objects.get(
                    id=agreement_id, user=user, service_package=package
                )
            else:
                agreement = ServiceAgreement.objects.filter(
                    user=user, service_package=package, active=True
                ).order_by('-date_created').first()
            if agreement:
                if not agreement.active:
                    agreement.active = True
                    if not agreement.start_date:
                        agreement.start_date = datetime.now().date()
                    agreement.save()
                if agreement.property and not agreement.property.is_active:
                    agreement.property.is_active = True
                    agreement.property.has_active_service = True
                    agreement.property.save()
        except ServiceAgreement.DoesNotExist:
            messages.error(
                request,
                "Subscription agreement not found. Please contact support."
            )
            return redirect("package_selection")
        try:
            create_subscription_job(agreement, package)
        except Exception as e:
            logger.error(f"Failed to create job: {e}", exc_info=True)
            messages.warning(
                request,
                "Subscription created, but job setup failed. Please contact "
                "support."
            )
        try:
            dashboard_url = request.build_absolute_uri(
                reverse('account_dashboard')
            )
            subject = f"Subscription Confirmation - {package.name}"
            html_content = render_to_string(
                'emails/package_confirmation_email.html',
                {
                    'user': user,
                    'package': package,
                    'agreement': agreement,
                    'dashboard_url': dashboard_url,
                }
            )
            text_content = strip_tags(html_content)
            user_email = EmailMultiAlternatives(
                subject, text_content, 'noreply@dsproperty.com', [user.email]
            )
            user_email.attach_alternative(html_content, "text/html")
            user_email.send()
        except Exception as e:
            logger.error(
                f"Failed to send confirmation email to {user.email}: {e}",
                exc_info=True
            )
        try:
            superusers = User.objects.filter(is_superuser=True).values_list(
                'email', flat=True
            )
            if superusers:
                subject = (
                    f"New Subscription: {user.get_full_name()} - {package.name}"
                )
                admin_context = {
                    'user_name': user.get_full_name() or user.username,
                    'user_email': user.email,
                    'package_name': package.name,
                    'package_price': package.price_usd,
                    'property_label': getattr(
                        agreement.property, 'label', 'N/A'
                    ),
                    'property_address_summary': getattr(
                        agreement.property, 'address_summary', 'N/A'
                    ),
                    'start_date': (
                        agreement.start_date.strftime('%B %d, %Y')
                        if agreement.start_date else 'N/A'
                    ),
                    'stripe_subscription_id': (
                        agreement.stripe_subscription_id or 'N/A'
                    ),
                    'stripe_customer_id': (
                        agreement.stripe_customer_id or 'N/A'
                    ),
                    'site_name': 'DS Property Group',
                }
                admin_html = render_to_string(
                    'emails/office_notification_email.html', admin_context
                )
                admin_text = strip_tags(admin_html)
                admin_email = EmailMultiAlternatives(
                    subject, admin_text, 'noreply@dsproperty.com', list(superusers)
                )
                admin_email.attach_alternative(admin_html, "text/html")
                admin_email.send()
        except Exception as e:
            logger.error(f"Failed to notify superusers: {e}", exc_info=True)
    subscription_start_date_display = (
        agreement.start_date.strftime("%B %d, %Y")
        if agreement and agreement.start_date else "Unknown"
    )
    amount_paid_display = (
        f"{agreement.amount_paid:.2f}"
        if agreement and agreement.amount_paid else "0.00"
    )
    context = {
        'package': package,
        'agreement': agreement,
        'amount_paid_display': amount_paid_display,
        'subscription_start_date_display': subscription_start_date_display,
    }
    return render(request, 'memberships/subscription_success.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def resend_confirmation_email(request, agreement_id):
    """
    Allows a user to resend their subscription confirmation email.
    """
    user = request.user
    agreement = get_object_or_404(ServiceAgreement, id=agreement_id, user=user)
    package = agreement.service_package
    subscription_start_date_display = (
        agreement.start_date.strftime("%B %d, %Y")
        if agreement.start_date else datetime.now().strftime("%B %d, %Y")
    )
    amount_paid_display = (
        f"{agreement.amount_paid:.2f}"
        if agreement.amount_paid is not None else "0.00"
    )
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
            html_message = render_to_string(
                'emails/package_confirmation_email.html', email_context
            )
            plain_message = strip_tags(html_message)
            pdf_file_name = 'dsp-terms-conditions.pdf'
            pdf_path = os.path.join(
                settings.BASE_DIR, 'static', 'pdfs', pdf_file_name
            )
            pdf_attachment = None
            if not os.path.exists(pdf_path):
                logger.error(
                    f"PDF file not found at: {pdf_path}. Cannot attach terms "
                    f"and conditions."
                )
            else:
                with open(pdf_path, 'rb') as pdf_file:
                    pdf_data = pdf_file.read()
                pdf_attachment = (
                    pdf_file_name, pdf_data, 'application/pdf'
                )
            user_email = EmailMultiAlternatives(
                subject=(
                    f"Welcome to {email_context['site_name']}! "
                    f"Your Subscription is Confirmed - Terms Included"
                ),
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            user_email.attach_alternative(html_message, "text/html")
            if pdf_attachment:
                user_email.attach(*pdf_attachment)
            user_email.send(fail_silently=False)
            messages.success(request, "Confirmation email resent successfully!")
            logger.info(
                f"Subscription confirmation email (with PDF) resent to "
                f"{user.email} for agreement {agreement.id}."
            )
        except Exception as e:
            logger.error(
                f"Failed to resend subscription confirmation email to "
                f"{user.email}: {e}", exc_info=True
            )
            messages.error(
                request,
                "Failed to resend confirmation email. Please contact support."
            )
    else:
        messages.warning(
            request,
            "Cannot resend email: No email address associated with your account."
        )
    return redirect('account_dashboard')


@login_required
@require_POST
@user_passes_test(lambda u: u.is_superuser)
def cancel_agreement(request, agreement_id):
    """
    Cancels a service agreement and its Stripe subscription.
    Sends a cancellation confirmation email with only package, property address,
    and cancellation date.
    """
    user = request.user
    agreement = get_object_or_404(ServiceAgreement, id=agreement_id)
    if not request.user.is_staff and agreement.user != request.user:
        messages.error(
            request, "You do not have permission to cancel this agreement."
        )
        return redirect('all_subscriptions')
    if not agreement.active:
        messages.info(
            request,
            f"Agreement {agreement.id} is already inactive. No action taken."
        )
        return redirect('all_subscriptions')
    try:
        with transaction.atomic():
            stripe_cancellation_successful_or_already_cancelled = False
            if agreement.stripe_subscription_id:
                try:
                    subscription = stripe.Subscription.retrieve(
                        agreement.stripe_subscription_id
                    )
                    if subscription.status not in ['canceled', 'ended']:
                        stripe.Subscription.modify(
                            agreement.stripe_subscription_id,
                            cancel_at_period_end=True
                        )
                        logger.info(
                            f"Stripe subscription {agreement.stripe_subscription_id} "
                            f"scheduled for cancellation at period end for agreement "
                            f"{agreement.id}."
                        )
                        messages.success(
                            request,
                            f"Your service with ID {agreement.stripe_subscription_id} "
                            f"is scheduled to be cancelled at the end of its current "
                            f"billing period."
                        )
                        stripe_cancellation_successful_or_already_cancelled = True
                    else:
                        logger.warning(
                            f"Stripe subscription {agreement.stripe_subscription_id} "
                            f"was already cancelled or ended in Stripe. Local DB will "
                            f"be updated."
                        )
                        messages.info(
                            request,
                            f"Your service with ID {agreement.stripe_subscription_id} "
                            f"was already cancelled or ended in our payment system. "
                            f"Updating your account details."
                        )
                        stripe_cancellation_successful_or_already_cancelled = True
                except stripe.error.InvalidRequestError as e:
                    logger.warning(
                        f"Stripe subscription {agreement.stripe_subscription_id} not "
                        f"found or already cancelled in Stripe: {e}. Local DB will be "
                        f"updated."
                    )
                    messages.info(
                        request,
                        f"Your service with ID {agreement.stripe_subscription_id} "
                        f"could not be found or was already cancelled in our payment "
                        f"system. Your account details will be updated."
                    )
                    stripe_cancellation_successful_or_already_cancelled = True
                except Exception as e:
                    logger.error(
                        f"Error communicating with Stripe for agreement "
                        f"{agreement.id}: {e}", exc_info=True
                    )
                    messages.error(
                        request,
                        f"Failed to communicate with our payment system regarding "
                        f"your subscription: {e}. Please try again or contact support."
                    )
                    raise
            else:
                logger.warning(
                    f"Agreement {agreement.id} has no Stripe subscription ID. "
                    f"Proceeding with local cancellation."
                )
                messages.info(
                    request,
                    "This service did not have an active subscription in our "
                    "payment system. Updating your account details."
                )
                stripe_cancellation_successful_or_already_cancelled = True
            if stripe_cancellation_successful_or_already_cancelled:
                agreement.active = False
                agreement.end_date = timezone.now().date()
                agreement.status = 'cancelled'
                agreement.save()
                logger.info(
                    f"ServiceAgreement {agreement.id} marked as cancelled in local "
                    f"database."
                )
                prop = getattr(agreement, 'property', None)
                if prop:
                    other_active = ServiceAgreement.objects.filter(
                        property=prop, active=True
                    ).exclude(id=agreement.id).exists()
                    if not other_active:
                        prop.has_active_service = False
                        prop.stripe_subscription_id = None
                        prop.save()
                        logger.info(
                            f"Property {prop.id} updated: has_active_service=False, "
                            f"subscription cleared."
                        )
                    else:
                        logger.info(
                            f"Property {prop.id} still has other active agreements."
                        )
                # --- Only this email context and sending block changed below! ---
                email_context = {
                    'package_name': (
                        agreement.service_package.name
                        if agreement.service_package else ''
                    ),
                    'property_address': (
                        prop.address_summary if prop else ''
                    ),
                    'cancellation_date': timezone.now().strftime("%B %d, %Y"),
                }
                if user.email:
                    try:
                        html_message = render_to_string(
                            'emails/subscription_cancellation_confirmation.html',
                            email_context
                        )
                        plain_message = strip_tags(html_message)
                        email = EmailMultiAlternatives(
                            subject=(
                                f"Confirmation: Your "
                                f"{email_context['package_name']} "
                                f"Service Has Been Cancelled"
                            ),
                            body=plain_message,
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            to=[user.email],
                        )
                        email.attach_alternative(html_message, "text/html")
                        email.send()
                        logger.info(
                            f"Sent cancellation confirmation email to {user.email} "
                            f"for agreement {agreement.id}."
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to send cancellation confirmation email for "
                            f"agreement {agreement.id}: {e}", exc_info=True
                        )
                        messages.warning(
                            request,
                            "Cancellation succeeded, but confirmation email failed "
                            "to send. Please contact support."
                        )
                else:
                    logger.warning(
                        f"Agreement {agreement.id} cancelled but user has no email "
                        f"address."
                    )
                    messages.warning(
                        request,
                        "Your service was cancelled, but no email confirmation "
                        "could be sent (no email on file)."
                    )
            if not messages.get_messages(request):
                messages.success(
                    request,
                    f"Your '{getattr(agreement.service_package, 'name', 'service')}' "
                    f"has been successfully cancelled."
                )
    except stripe.error.StripeError as e:
        logger.error(
            f"A critical Stripe API error occurred during cancellation for agreement "
            f"{agreement.id}: {e}", exc_info=True
        )
        messages.error(
            request,
            f"A critical error occurred with our payment system: {e}. Please "
            "contact support."
        )
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during cancellation for agreement "
            f"{agreement.id}: {e}", exc_info=True
        )
        messages.error(
            request,
            "An unexpected error occurred during cancellation. Please contact "
            "support."
        )
    return redirect('all_subscriptions')


logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Handles Stripe webhook events for subscriptions and one-off quotes.
    """
    from quote_requests.models import QuoteRequest
    from django.contrib.auth import get_user_model

    User = get_user_model()

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        logger.info(f"🔔 Received event: {event['type']}")
    except ValueError as e:
        logger.error(f"⚠️ Invalid payload: {e}", exc_info=True)
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"⚠️ Invalid signature: {e}", exc_info=True)
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"⚠️ Unexpected error: {e}", exc_info=True)
        return HttpResponse(status=500)

    # Handle one-off quote payment (Checkout and PaymentIntent)
    quote_id = None
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        metadata = session.get('metadata', {})
        quote_id = metadata.get('quote_id')
    elif event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        metadata = intent.get('metadata', {})
        quote_id = metadata.get('quote_id')

    if quote_id:
        try:
            from quote_requests.utils import create_one_off_job_from_quote
            quote = QuoteRequest.objects.get(pk=quote_id)
            if quote.status != 'PAID':
                quote.status = 'PAID'
                quote.payment_status = 'PAID'
                quote.save()
                create_one_off_job_from_quote(quote)
                logger.info(f"✅ One-off job created for paid quote {quote.id}")
            else:
                logger.info(
                    f"Quote {quote.id} already marked as PAID, skipping job creation."
                )
        except Exception as e:
            logger.error(
                f"❌ Error handling quote payment for quote_id={quote_id}: {e}",
                exc_info=True
            )
            return HttpResponse(status=500)
        return HttpResponse(status=200)

    # Handle subscription events
    if event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        metadata = subscription.get('metadata', {})
        user_id = metadata.get('user_id')
        property_id = metadata.get('property_id')
        package_id = metadata.get('package_id')

        if not all([user_id, property_id, package_id]):
            return HttpResponse(status=400)

        try:
            user = User.objects.get(id=user_id)
            prop = Property.objects.get(id=property_id)
            service_package = ServicePackage.objects.get(id=package_id)

            ServiceAgreement.objects.filter(
                property=prop, active=True
            ).update(
                active=False, end_date=timezone.now().date()
            )

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
                        subscription['current_period_end'],
                        tz=timezone.utc
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

            prop.stripe_subscription_id = subscription['id']
            prop.has_active_service = True
            prop.save()

        except Exception as e:
            logger.error(
                f"Error handling customer.subscription.created: {e}",
                exc_info=True
            )
            return HttpResponse(status=400)

    elif event['type'] in [
        'customer.subscription.deleted', 'customer.subscription.updated'
    ]:
        subscription = event['data']['object']
        try:
            agreement = ServiceAgreement.objects.get(
                stripe_subscription_id=subscription['id']
            )
            if subscription['status'] == 'canceled':
                agreement.active = False
                agreement.end_date = timezone.now().date()
                agreement.status = 'cancelled'
            elif subscription['status'] == 'active':
                agreement.active = True
                agreement.status = 'active'
                agreement.stripe_current_period_end = timezone.datetime.fromtimestamp(
                    subscription['current_period_end'], tz=timezone.utc
                ).date()
            else:
                agreement.active = False
                agreement.status = subscription['status']
                agreement.end_date = timezone.now().date()
            agreement.save()
            if agreement.property:
                others = ServiceAgreement.objects.filter(
                    property=agreement.property, active=True
                ).exclude(id=agreement.id).exists()
                if not others and not agreement.active:
                    agreement.property.has_active_service = False
                    agreement.property.stripe_subscription_id = None
                elif agreement.active:
                    agreement.property.has_active_service = True
                    agreement.property.stripe_subscription_id = subscription['id']
                agreement.property.save()
        except ServiceAgreement.DoesNotExist:
            logger.warning(
                f"ServiceAgreement not found for {event['type']} - "
                f"{subscription['id']}"
            )
            return HttpResponse(status=200)

    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        subscription_id = invoice.get('subscription')
        if subscription_id:
            try:
                agreement = ServiceAgreement.objects.get(
                    stripe_subscription_id=subscription_id
                )
                agreement.active = True
                agreement.status = 'active'
                agreement.amount_paid_last_invoice = (
                    invoice.get('amount_paid') / 100.0
                )
                agreement.last_payment_date = timezone.datetime.fromtimestamp(
                    invoice['created'], tz=timezone.utc
                ).date()
                if invoice.get('period_end'):
                    agreement.stripe_current_period_end = (
                        timezone.datetime.fromtimestamp(
                            invoice['period_end'], tz=timezone.utc
                        ).date()
                    )
                agreement.save()
                if agreement.property:
                    agreement.property.has_active_service = True
                    agreement.property.stripe_subscription_id = subscription_id
                    agreement.property.save()
                subject = f"Your Service Subscription is Active"
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
                from django.core.mail import EmailMessage
                email = EmailMessage(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [agreement.user.email],
                )
                email.attach_alternative(html_message, "text/html")
                pdf_file_name = 'dsp-terms-conditions.pdf'
                pdf_path = os.path.join(
                    settings.BASE_DIR, 'static', 'pdfs', pdf_file_name
                )
                if os.path.exists(pdf_path):
                    with open(pdf_path, 'rb') as pdf_file:
                        pdf_data = pdf_file.read()
                    email.attach(
                        pdf_file_name, pdf_data, 'application/pdf'
                    )
                email.send(fail_silently=True)
            except ServiceAgreement.DoesNotExist:
                logger.warning(
                    f"Invoice payment succeeded for unknown subscription "
                    f"{subscription_id}"
                )
    return HttpResponse(status=200)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def all_subscriptions(request):
    """
    Displays all active service agreements (subscriptions) for staff/superusers.
    """
    agreements = ServiceAgreement.objects.select_related(
        'user', 'service_package', 'property'
    ).filter(active=True).order_by('-date_created')
    return render(
        request, 'memberships/all_subscriptions.html',
        {'agreements': agreements}
    )


@login_required
def sidebar_fragment(request):
    """
    Renders a fragment for the sidebar, likely showing current subscriptions or
    property status. Should be included via template.
    """
    user_properties = Property.objects.filter(
        profile__user=request.user, is_active=True
    ).prefetch_related(
        Prefetch(
            'serviceagreement_set',
            queryset=ServiceAgreement.objects.filter(
                active=True
            ).select_related('service_package'),
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
