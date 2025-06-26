from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from memberships.models import ServicePackage
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseNotFound


# ---------- STATIC PAGES ----------

def index(request):
    """Return the home page with VAPID key for web push notifications."""
    context = {
        'vapid_public_key': settings.WEBPUSH_SETTINGS['VAPID_PUBLIC_KEY']
    }
    return render(request, 'home/index.html', context)


def contact(request):
    """Return the contact page."""
    return render(request, 'home/contact.html')


def border_2_border(request):
    """Return the Border 2 Border page."""
    return render(request, 'home/border-2-border.html')


def splashzone_pools(request):
    """Return the Splash Zone Pools page."""
    return render(request, 'home/splash-zone-pools.html')


# ---------- ERROR HANDLING ----------

def custom_404_view(request, exception=None):
    """Handle 404 errors with a custom page."""
    return render(request, 'home/404.html', status=404)


def custom_500_view(request):
    """Handle 500 errors with a custom page."""
    return render(request, 'home/500.html', status=500)


def trigger_404(request):
    """Manually trigger a 404 page (for testing)."""
    return HttpResponseNotFound(render(request, 'home/404.html', status=404))


def trigger_500(request):
    """Manually trigger a 500 error (for testing)."""
    raise Exception("Simulated server error for testing 500 page")


# ---------- SERVICE PACKAGE MANAGEMENT ----------

class SuperuserRequiredMixin(UserPassesTestMixin):
    """Mixin to restrict views to superusers only."""
    def test_func(self):
        return self.request.user.is_superuser


class ServicePackageListView(ListView):
    """View to list all service packages."""
    model = ServicePackage
    template_name = 'memberships/servicepackage_list.html'
    context_object_name = 'packages'


class ServicePackageCreateView(SuperuserRequiredMixin, CreateView):
    """View to create a new service package."""
    model = ServicePackage
    fields = ['name', 'category', 'tier', 'price_usd', 'description', 'is_active', 'stripe_price_id']
    template_name = 'memberships/form.html'
    success_url = reverse_lazy('servicepackage_list')


class ServicePackageUpdateView(SuperuserRequiredMixin, UpdateView):
    """View to update an existing service package."""
    model = ServicePackage
    fields = ['name', 'category', 'tier', 'price_usd', 'description', 'is_active', 'stripe_price_id']
    template_name = 'memberships/form.html'
    success_url = reverse_lazy('servicepackage_list')


class ServicePackageDeleteView(SuperuserRequiredMixin, DeleteView):
    """View to delete a service package."""
    model = ServicePackage
    template_name = 'memberships/servicepackage_confirm_delete.html'
    success_url = reverse_lazy('servicepackage_list')


def privacy_policy(request):
    return render(request, "privacy_policy.html")
