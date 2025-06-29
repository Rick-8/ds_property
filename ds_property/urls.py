from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.views.static import serve
from staff_pwa import views
from staff_pwa.views import OfflinePageView
import os

urlpatterns = [
    # PWA essential routes
    path(
        'manifest.json',
        TemplateView.as_view(
            template_name="staff_pwa/manifest.json",
        ),
        name='manifest'
    ),
    re_path(
        r'^serviceworker\.js$',
        serve,
        {
            'path': 'serviceworker.js',
            'document_root': settings.BASE_DIR,
        }
    ),
    path('offline/', OfflinePageView.as_view(), name='offline'),
    path('splash/', views.pwa_splash, name='pwa_splash'),

    # --- Serve favicon.ico ---
    path(
        'favicon.ico',
        serve,
        {
            'path': 'media/favicon.ico',
            'document_root': os.path.join(settings.BASE_DIR, 'static'),
        }
    ),

    # --- Serve sitemap.xml ---
    path(
        'sitemap.xml',
        serve,
        {
            'path': 'sitemap.xml',
            'document_root': r'C:\Users\rick_\Documents\vscode-projects\ds_property',
        }
    ),

    # Auth and apps
    path('account/', include('allauth.urls')),
    path('accounts/', include('accounts.urls')),
    path('pwa/', include('staff_pwa.urls')),
    path('quotes/', include('quote_requests.urls')),
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('memberships/', include('memberships.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('staff/', include('staff_portal.urls')),
    path('management/', include('management.urls')),
    path('webpush/', include('webpush.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
