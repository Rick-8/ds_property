from django.urls import path
from . import views
from .views import list_all_properties

urlpatterns = [
    path('profile/', views.view_profile, name='view_profile'),
    path('properties/', views.list_properties, name='list_properties'),
    path('properties/add/', views.add_property, name='add_property'),
    path('properties/edit/<int:property_id>/', views.edit_property, name='edit_property'),
    path('properties/delete/<int:property_id>/', views.delete_property, name='delete_property'),
    path('dashboard/', views.account_dashboard, name='account_dashboard'),
    path('properties/all/', list_all_properties, name='list_all_properties'),
]
