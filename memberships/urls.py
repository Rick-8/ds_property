from django.urls import path
from . import views

urlpatterns = [
    path('memberships/', views.servicepackage_list, name='servicepackage_list'),
    path('memberships/create/', views.package_create, name='servicepackage_create'),
    path('memberships/update/<int:pk>/', views.package_update, name='servicepackage_update'),
    path('memberships/delete/<int:pk>/', views.package_delete, name='servicepackage_delete'),
]
