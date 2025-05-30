from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from memberships.models import ServicePackage
from django.shortcuts import render
from django.http import HttpResponseNotFound


def index(request):
    """ A view to return the index page """
    return render(request, 'home/index.html')


def contact(request):
    """ A view to return the contact page """
    return render(request, 'home/contact.html')


def border_2_border(request):
    """ A view to return the Border 2 Border page """
    return render(request, 'border-2-border.html')


def splashzone_pools(request):
    """ A view to return the Splash Zone Pools page """
    return render(request, 'splash-zone-pools.html')


def custom_404_view(request, exception=None):
    return render(request, "404.html", status=404)


def custom_500_view(request):
    return render(request, "500.html", status=500)


class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class ServicePackageListView(ListView):
    model = ServicePackage
    template_name = 'memberships/servicepackage_list.html' # Keep this as is, assuming it exists
    context_object_name = 'packages'


class ServicePackageCreateView(SuperuserRequiredMixin, CreateView):
    model = ServicePackage
    fields = ['name', 'category', 'tier', 'price_usd', 'description', 'is_active', 'stripe_price_id']
    # CORRECTED: Point to the existing form.html
    template_name = 'memberships/form.html'
    success_url = reverse_lazy('servicepackage_list') # Assuming 'servicepackage_list' is in home/urls.py


class ServicePackageUpdateView(SuperuserRequiredMixin, UpdateView):
    model = ServicePackage
    fields = ['name', 'category', 'tier', 'price_usd', 'description', 'is_active', 'stripe_price_id']
    # CORRECTED: Point to the existing form.html
    template_name = 'memberships/form.html'
    success_url = reverse_lazy('servicepackage_list') # Assuming 'servicepackage_list' is in home/urls.py


class ServicePackageDeleteView(SuperuserRequiredMixin, DeleteView):
    model = ServicePackage
    template_name = 'memberships/servicepackage_confirm_delete.html' # Keep this as is, assuming it exists
    success_url = reverse_lazy('servicepackage_list')


# Optional test-only views to simulate errors:
def trigger_404(request):
    return HttpResponseNotFound(render(request, "404.html", status=404))


def trigger_500(request):
    raise Exception("Simulated server error for testing 500 page")
