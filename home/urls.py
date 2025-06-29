from home.views import trigger_404, trigger_500
from django.urls import path, include
from django.contrib import admin
from . import views


urlpatterns = [
    path('', views.index, name='home'),
    path('contact/', views.contact, name='contact'),
    path('border-2-border/', views.border_2_border, name='border-2-border'),
    path('splashzone/', views.splashzone_pools, name='splashzone_pools'),
    path("test-500/", trigger_500, name="test_500"),
    path('', views.ServicePackageListView.as_view(), name='servicepackage_list'),
    path('create/', views.ServicePackageCreateView.as_view(), name='servicepackage_create'),
    path('<int:pk>/edit/', views.ServicePackageUpdateView.as_view(), name='servicepackage_update'),
    path('<int:pk>/delete/', views.ServicePackageDeleteView.as_view(), name='servicepackage_delete'),
    path('webpush/', include('webpush.urls')),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('cookie-policy/', views.cookie_policy, name='cookie_policy'),

]
