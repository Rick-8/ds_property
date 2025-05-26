from .views import create_checkout_session
from django.urls import path
from . import views

urlpatterns = [
    path('', views.servicepackage_list, name='servicepackage_list'),
    path('create/', views.package_create, name='servicepackage_create'),
    path('update/<int:pk>/', views.package_update, name='servicepackage_update'),
    path('delete/<int:pk>/', views.package_delete, name='servicepackage_delete'),
    path('select-package/', views.package_selection, name='package_selection'),
    path('select-package/<int:package_id>/', views.select_package, name='select_package'),
    path('confirm-contract/<int:package_id>/', views.confirm_contract, name='confirm_contract'),
    path('remove-package/<int:package_id>/', views.remove_package, name='remove_package'),
    path('update-package-property/<int:package_id>/', views.update_package_property, name='update_package_property'),
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('payment/<int:package_id>/', views.payment, name='payment'),
    path('subscription-success/', views.subscription_success, name='subscription_success'),

    # route for AJAX sidebar content fetching
    path('sidebar-fragment/', views.sidebar_fragment, name='sidebar_fragment'),
]
