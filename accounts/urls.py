from .views import newsletter_crud_list, newsletter_crud_edit, newsletter_crud_delete
from django.urls import path
from . import views
from .views import list_all_properties
from .views import newsletter_signup

urlpatterns = [
    path('profile/', views.view_profile, name='view_profile'),
    path('properties/', views.list_properties, name='list_properties'),
    path('properties/add/', views.add_property, name='add_property'),
    path('properties/edit/<int:property_id>/', views.edit_property, name='edit_property'),
    path('properties/delete/<int:property_id>/', views.delete_property, name='delete_property'),
    path('dashboard/', views.account_dashboard, name='account_dashboard'),
    path('properties/all/', list_all_properties, name='list_all_properties'),
    path('newsletter-signup/', newsletter_signup, name='newsletter_signup'),
    path('newsletter-crud/edit/<int:pk>/', newsletter_crud_edit, name='newsletter_crud_edit'),
    path('newsletter-crud/delete/<int:pk>/', newsletter_crud_delete, name='newsletter_crud_delete'),
    path('newsletter-dashboard/', views.newsletter_crud_dashboard, name='newsletter_crud_dashboard'),
]
