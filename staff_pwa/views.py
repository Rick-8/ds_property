from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.shortcuts import render


@login_required
def pwa_splash(request):
    return render(request, 'staff_pwa/pwa_splash.html')


class OfflinePageView(TemplateView):
    template_name = "staff_pwa/offline.html"
