import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from memberships.models import ServiceAgreement


logger = logging.getLogger(__name__)


def send_package_signup_confirmation(request, user_email, user_name, package_details):
    """
    Sends a confirmation email to the user after a successful package signup.
    """
    subject = f"Your {package_details['name']} Subscription is Confirmed!"

    html_message = render_to_string('emails/package_confirmation_email.html', {
        'user_name': user_name,
        'package_name': package_details['name'],
        'package_price': package_details['price'],
        'start_date': package_details['start_date'],
        'site_name': settings.SITE_NAME,
        'support_email': settings.DEFAULT_FROM_EMAIL,
        'current_year': timezone.now().year,
        'request': request,
    })

    plain_message = f"""
Dear {user_name},

Thank you for subscribing to our {package_details['name']} package!

Your service started on {package_details['start_date']} and your first payment of £{package_details['price']:.2f} has been processed successfully.

You can manage your subscription and view details in your account dashboard at:
{request.build_absolute_uri(reverse('subscription_success'))}

If you have any questions, please don't hesitate to contact us at {settings.DEFAULT_FROM_EMAIL}.

Sincerely,
The {settings.SITE_NAME} Team
"""

    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Confirmation email sent to {user_email} for package {package_details['name']}.")
    except Exception as e:
        logger.error(f"Failed to send confirmation email to {user_email}: {e}", exc_info=True)


def send_office_signup_notification(user, package, property_obj, agreement):
    """
    Sends a notification email to the office/admin about a new service package signup.
    """
    if not hasattr(settings, 'OFFICE_NOTIFICATION_EMAIL') or not settings.OFFICE_NOTIFICATION_EMAIL:
        logger.warning("OFFICE_NOTIFICATION_EMAIL is not configured in settings. Cannot send office notification.")
        return

    subject = f"New Service Package Signup: {package.name} for {property_obj.label}"

    html_message = render_to_string('emails/office_notification_email.html', {
        'user_name': user.get_full_name() or user.username,
        'user_email': user.email,
        'package_name': package.name,
        'package_price': float(package.price_usd),
        'property_label': property_obj.label,
        'property_address_summary': property_obj.address_summary,
        'start_date': agreement.start_date.strftime('%Y-%m-%d'),
        'stripe_subscription_id': agreement.stripe_subscription_id,
        'stripe_customer_id': agreement.stripe_customer_id,
        'site_name': settings.SITE_NAME,
        'current_year': timezone.now().year,
    })

    plain_message = f"""
Hello Admin,

A new customer has just signed up for a service package via the website. Here are the details:

Customer Name: {user.get_full_name() or user.username}
Customer Email: {user.email}
Service Package: {package.name}
Package Price: £{float(package.price_usd):.2f}
Property: {property_obj.label} ({property_obj.address_summary})
Subscription Start Date: {agreement.start_date.strftime('%Y-%m-%d')}
Stripe Subscription ID: {agreement.stripe_subscription_id}
Stripe Customer ID: {agreement.stripe_customer_id}

Please log into the Stripe Dashboard and your Django Admin to verify and manage this new subscription and property.

Thank you,
The Automated {settings.SITE_NAME} Notification System
"""

    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.OFFICE_NOTIFICATION_EMAIL],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Office notification email sent for new signup: {user.email} - {package.name}.")
    except Exception as e:
        logger.error(f"Failed to send office notification email for {user.email}: {e}", exc_info=True)