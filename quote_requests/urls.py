from django.urls import path
from . import views

urlpatterns = [
    path('admin/', views.admin_quote_list, name='admin_quote_list'),
    path('admin/<int:pk>/', views.quote_detail_view, name='quote_detail'),
    path('admin/<int:pk>/accept/', views.accept_quote, name='accept_quote'),
    path('admin/<int:pk>/decline/', views.decline_quote, name='decline_quote'),
    path('request/', views.request_quote_view, name='request_quote'),
    path('quotes/<int:pk>/update-notes/', views.update_quote_notes, name='update_quote_notes'),
    path('quotes/<int:pk>/update-items/', views.update_quote_items, name='update_quote_items'),
    path('quotes/<int:pk>/mark-reviewed/', views.mark_quote_reviewed, name='mark_quote_reviewed'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('quotes/thank-you/', views.payment_thank_you, name='payment_thank_you'),
    path('quotes/cancel/', views.payment_cancelled, name='payment_cancelled'),
    path('quotes/thank-you/', views.payment_thank_you, name='payment_thank_you'),
    path('my-quotes/', views.my_quotes, name='my_quotes'),

]
