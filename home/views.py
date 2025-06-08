from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from memberships.models import ServicePackage
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseNotFound


def index(request):
    """A view to return the index page with VAPID key for push notifications."""
    context = {
        'vapid_public_key': settings.WEBPUSH_SETTINGS['VAPID_PUBLIC_KEY']
    }
    return render(request, 'home/index.html', context)


def contact(request):
    """A view to return the contact page."""
    return render(request, 'home/contact.html')


def border_2_border(request):
    """A view to return the Border 2 Border page."""
    return render(request, 'border-2-border.html')


def splashzone_pools(request):
    """A view to return the Splash Zone Pools page."""
    return render(request, 'splash-zone-pools.html')


def custom_404_view(request, exception=None):
    """A view to handle 404 errors."""
    return render(request, "404.html", status=404)


def custom_500_view(request):
    """A view to handle 500 errors."""
    return render(request, "500.html", status=500)


class SuperuserRequiredMixin(UserPassesTestMixin):
    """Mixin to restrict access to superusers only."""

    def test_func(self):
        return self.request.user.is_superuser


class ServicePackageListView(ListView):
    """View to list all service packages."""
    model = ServicePackage
    template_name = 'memberships/servicepackage_list.html'
    context_object_name = 'packages'


class ServicePackageCreateView(SuperuserRequiredMixin, CreateView):
    """View to allow superusers to create service packages."""
    model = ServicePackage
    fields = ['name', 'category', 'tier', 'price_usd', 'description', 'is_active', 'stripe_price_id']
    template_name = 'memberships/form.html'
    success_url = reverse_lazy('servicepackage_list')


class ServicePackageUpdateView(SuperuserRequiredMixin, UpdateView):
    """View to allow superusers to update existing service packages."""
    model = ServicePackage
    fields = ['name', 'category', 'tier', 'price_usd', 'description', 'is_active', 'stripe_price_id']
    template_name = 'memberships/form.html'
    success_url = reverse_lazy('servicepackage_list')


class ServicePackageDeleteView(SuperuserRequiredMixin, DeleteView):
    """View to allow superusers to delete a service package."""
    model = ServicePackage
    template_name = 'memberships/servicepackage_confirm_delete.html'
    success_url = reverse_lazy('servicepackage_list')


def trigger_404(request):
    """Optional view to simulate a 404 error."""
    return HttpResponseNotFound(render(request, "404.html", status=404))


def trigger_500(request):
    """Optional view to simulate a 500 error."""
    raise Exception("Simulated server error for testing 500 page")
