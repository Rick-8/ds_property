from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile, Property
from .forms import ProfileForm, PropertyForm


@login_required
def view_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('index')  # or wherever you want to redirect
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileForm(instance=profile, user=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def list_properties(request):
    properties = request.user.profile.property_set.all()  # or properties.all() if related_name set
    return render(request, 'accounts/property_list.html', {'properties': properties})


@login_required
def add_property(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            property = form.save(commit=False)
            property.profile = request.user.profile
            property.save()
            messages.success(request, 'Property added successfully.')
            return redirect('list_properties')
    else:
        form = PropertyForm()
    return render(request, 'accounts/property_form.html', {'form': form, 'title': 'Add Property'})


@login_required
def edit_property(request, property_id):
    property = get_object_or_404(Property, id=property_id, profile=request.user.profile)
    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property)
        if form.is_valid():
            form.save()
            messages.success(request, 'Property updated successfully.')
            return redirect('list_properties')
    else:
        form = PropertyForm(instance=property)
    return render(request, 'accounts/property_form.html', {'form': form, 'title': 'Edit Property'})
