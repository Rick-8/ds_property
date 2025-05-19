from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.view_profile, name='view_profile'),
    path('properties/', views.list_properties, name='list_properties'),
    path('properties/add/', views.add_property, name='add_property'),
    path('properties/edit/<int:property_id>/', views.edit_property, name='edit_property'),
    path('properties/delete/<int:property_id>/', views.delete_property, name='delete_property'),
]
