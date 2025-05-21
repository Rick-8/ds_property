from django.shortcuts import render
from django.http import HttpResponseServerError, HttpResponseNotFound

# Create your views here.


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


# Optional test-only views to simulate errors:
def trigger_404(request):
    return HttpResponseNotFound(render(request, "404.html", status=404))


def trigger_500(request):
    raise Exception("Simulated server error for testing 500 page")
