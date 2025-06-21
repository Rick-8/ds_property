from django.urls import path
from . import views
from .views import view_quote_pdf, update_quote_description

urlpatterns = [
    path('custom-jobs/', views.admin_quote_list, name='admin_quote_list'),
    path('admin/<int:pk>/', views.quote_detail_view, name='quote_detail'),
    path('admin/<int:pk>/accept/', views.accept_quote, name='accept_quote'),
    path('admin/<int:pk>/decline/', views.decline_quote, name='decline_quote'),
    path('admin/<int:quote_id>/update-description/', update_quote_description, name='update_quote_description'),

    path('request/', views.request_quote_view, name='request_quote'),

    path('my-quotes/', views.my_quotes, name='my_quotes'),

    path('quotes/<int:pk>/update-notes/', views.update_quote_notes, name='update_quote_notes'),
    path('quotes/<int:pk>/update-items/', views.update_quote_items, name='update_quote_items'),
    path('quotes/<int:pk>/mark-reviewed/', views.mark_quote_reviewed, name='mark_quote_reviewed'),

    path('quotes/<int:quote_id>/create-payment-intent/', views.create_payment_intent, name='create_payment_intent'),
    path('quotes/payment-success/', views.payment_success, name='payment_success'),
    path('quotes/thank-you/', views.payment_thank_you, name='payment_thank_you'),
    path('quotes/cancel/', views.payment_cancelled, name='payment_cancelled'),

    path('pdf/<int:quote_id>/', view_quote_pdf, name='view_quote_pdf'),
    path('respond/<str:token>/', views.respond_to_quote, name='respond_to_quote'),
    path('respond/<str:token>/decline/', views.respond_decline_quote, name='respond_decline_quote'),
]
