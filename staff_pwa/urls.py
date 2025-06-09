from django.urls import path
from . import views

urlpatterns = [
    path('splash/', views.pwa_splash, name='pwa_splash'),
    path('offline/', views.OfflineView.as_view(), name='pwa_offline'),
]
