from django.urls import path, include
from django.shortcuts import render
from . import views

urlpatterns = [
    path('request/', views.request_quote_view, name='request_quote'),
    path('thanks/', lambda r: render(r, 'quote_requests/quote_thanks.html'), name='quote_thanks'),
    path('my-quotes/', views.quote_review_view, name='quote_review'),
    path('quote/<int:pk>/', views.quote_detail_view, name='quote_detail'),
]
