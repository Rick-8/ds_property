from django.urls import path
from .views import OfflinePageView
from . import views
from .views import ServiceWorkerView

urlpatterns = [
    path('splash/', views.pwa_splash, name='pwa_splash'),
    path("offline/", OfflinePageView.as_view(), name="offline"),
    path('serviceworker.js', ServiceWorkerView.as_view(), name='serviceworker'),
]
