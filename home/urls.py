from home.views import trigger_404, trigger_500
from django.urls import path
from django.contrib import admin
from . import views


urlpatterns = [
    path('', views.index, name='home'),
    path('contact/', views.contact, name='contact'),
    path('border-2-border/', views.border_2_border, name='border-2-border'),
    path('splashzone/', views.splashzone_pools, name='splashzone_pools'),
    path("test-404/", trigger_404, name="test_404"),
    path("test-500/", trigger_500, name="test_500"),
    path('', views.ServicePackageListView.as_view(), name='servicepackage_list'),
    path('create/', views.ServicePackageCreateView.as_view(), name='servicepackage_create'),
    path('<int:pk>/edit/', views.ServicePackageUpdateView.as_view(), name='servicepackage_update'),
    path('<int:pk>/delete/', views.ServicePackageDeleteView.as_view(), name='servicepackage_delete'),
]
