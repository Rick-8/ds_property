from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from django.conf import settings
import os


def pwa_splash(request):
    """Splash screen with animated intro and VAPID key injection"""
    return render(request, 'staff_pwa/pwa_splash.html', {
       'vapid_public_key': settings.VAPID_PUBLIC_KEY,
    })


class OfflinePageView(TemplateView):
    """Offline fallback page"""
    template_name = "staff_pwa/offline.html"


class ServiceWorkerView(View):
    """Serve the serviceworker.js correctly with headers"""

    def get(self, request):
        path = os.path.join(settings.BASE_DIR, 'static', 'js', 'serviceworker.js')
        try:
            with open(path, 'rb') as sw:
                response = HttpResponse(sw.read(), content_type='application/javascript')
                response["Service-Worker-Allowed"] = "/"
                return response
        except FileNotFoundError:
            return HttpResponse("Service Worker not found.", status=404)
