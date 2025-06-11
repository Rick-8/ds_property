from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.shortcuts import render
import os
from django.conf import settings
from django.http import HttpResponse
from django.views import View


@login_required
def pwa_splash(request):
    return render(request, 'staff_pwa/pwa_splash.html')


class OfflinePageView(TemplateView):
    template_name = "staff_pwa/offline.html"


class ServiceWorkerView(View):
    def get(self, request):
        path = os.path.join(settings.BASE_DIR, 'static', 'js', 'serviceworker.js')
        try:
            with open(path, 'rb') as sw:
                response = HttpResponse(sw.read(), content_type='application/javascript')
                response["Service-Worker-Allowed"] = "/"
                return response
        except FileNotFoundError:
            return HttpResponse("Service Worker not found.", status=404)
