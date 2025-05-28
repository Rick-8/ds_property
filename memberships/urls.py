# memberships/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Existing Service Package Management Views (All now present in views.py)
    path('', views.servicepackage_list, name='servicepackage_list'), # <-- UNCOMMENTED
    path('create/', views.package_create, name='servicepackage_create'),
    path('update/<int:pk>/', views.package_update, name='servicepackage_update'),
    path('delete/<int:pk>/', views.package_delete, name='servicepackage_delete'),

    # Package Selection and Contract Views (All now present in views.py)
    path('select-package/', views.package_selection, name='package_selection'),
    path('select-package/<int:package_id>/', views.select_package, name='select_package'),
    path('confirm-contract/<int:package_id>/', views.confirm_contract, name='confirm_contract'),
    # path('remove-package/<int:package_id>/', views.remove_package, name='remove_package'),
    path('update-package-property/<int:package_id>/', views.update_package_property, name='update_package_property'),

    # Core Stripe Subscription Flow Views (All now present in views.py)
    # The 'create-checkout-session' route is removed as it's no longer used.
    path('payment/<int:package_id>/', views.payment, name='payment'),
    path('subscription-success/', views.subscription_success, name='subscription_success'),
    path('subscription-cancel/', views.subscription_cancel, name='subscription_cancel'),

    # Other existing views (All now present in views.py)
    path('all-subscriptions/', views.all_subscriptions, name='all_subscriptions'),
    path('sidebar-fragment/', views.sidebar_fragment, name='sidebar_fragment'),

    # Webhook for Stripe payments (Already corrected and present in views.py)
    path('webhooks/stripe/', views.stripe_webhook, name='stripe_webhook'),
]