from django.urls import path
from .views import OfflinePageView
from . import views

urlpatterns = [
    path('splash/', views.pwa_splash, name='pwa_splash'),
    path("offline/", OfflinePageView.as_view(), name="offline"),
]
