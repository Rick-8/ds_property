"""
URL configuration for ds_property project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.generic import TemplateView
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('account/', include('allauth.urls')),
    path('', include('home.urls')),
    path('accounts/', include('accounts.urls')),
    path('memberships/', include('memberships.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('staff/', include('staff_portal.urls')),
    path("management/", include("management.urls")),
    path('webpush/', include('webpush.urls')),

    # ✅ Staff PWA app
    path('splash/', TemplateView.as_view(template_name='pwa_splash.html'), name='pwa_splash'),
    path('pwa/', include('staff_pwa.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
