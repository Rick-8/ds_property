from django.urls import path
from .views import pwa_splash, OfflinePageView, ServiceWorkerView

urlpatterns = [
    path('splash/', pwa_splash, name='pwa_splash'),
    path("offline/", OfflinePageView.as_view(), name="offline"),
    path('serviceworker.js', ServiceWorkerView.as_view(), name='serviceworker'),
]