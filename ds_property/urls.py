from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.generic import TemplateView
from django.conf.urls.static import static
from staff_pwa.views import OfflinePageView  # <-- Add this
import os

urlpatterns = [
    # Staff PWA manifest and serviceworker - place early so always available
    path('manifest.json', TemplateView.as_view(
        template_name="staff_pwa/manifest.json",
        content_type='application/json'),
        name='manifest'
    ),
    path('serviceworker.js', TemplateView.as_view(
        template_name="staff_pwa/serviceworker.js",
        content_type='application/javascript'),
        name='serviceworker'
    ),
    path('offline/', OfflinePageView.as_view(), name='offline'),  # <-- Add this
    path('splash/', TemplateView.as_view(template_name='pwa_splash.html'), name='pwa_splash'),
    path('pwa/', include('staff_pwa.urls')),

    # Standard app routes
    path('admin/', admin.site.urls),
    path('account/', include('allauth.urls')),
    path('', include('home.urls')),
    path('accounts/', include('accounts.urls')),
    path('memberships/', include('memberships.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('staff/', include('staff_portal.urls')),
    path('management/', include('management.urls')),
    path('webpush/', include('webpush.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
