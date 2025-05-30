from django.urls import path
from . import views

urlpatterns = [
    # Service Package Management Views
    path('', views.servicepackage_list, name='servicepackage_list'),
    path('create/', views.package_create, name='servicepackage_create'),
    path('delete/<int:pk>/', views.package_delete, name='servicepackage_delete'),

    # Package Selection and Contract Views
    path('select-package/', views.package_selection, name='package_selection'),
    path('select-package/<int:package_id>/', views.select_package, name='select_package'),
    path('confirm-contract/<int:package_id>/', views.confirm_contract, name='confirm_contract'),
    path('update-package-property/<int:package_id>/', views.update_package_property, name='update_package_property'),
    path('sidebar-fragment/', views.sidebar_fragment, name='sidebar_fragment'),
    path('agreements/<int:agreement_id>/resend-confirmation/', views.resend_confirmation_email, name='resend_confirmation_email'),

    # Core Stripe Subscription Flow Views
    path('payment/<int:package_id>/', views.payment, name='payment'),
    path('subscription-success/', views.subscription_success, name='subscription_success'),
    path('subscription-cancel/', views.subscription_cancel, name='subscription_cancel'),
    path('all-subscriptions/', views.all_subscriptions, name='all_subscriptions'),
    path('cancel-agreement/<int:agreement_id>/', views.cancel_agreement, name='cancel_agreement'),

    # Webhook for Stripe payments
    path('webhooks/stripe/', views.stripe_webhook, name='stripe_webhook'),
]
