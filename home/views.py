from django.shortcuts import render

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

