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
            return redirect('index')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileForm(instance=profile, user=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def list_properties(request):
    if request.user.is_staff or request.user.is_superuser:
        properties = Property.objects.all().order_by('route_number', 'label')
    else:
        properties = request.user.profile.properties.all().order_by('label')
    return render(request, 'accounts/property_list.html', {
        'properties': properties,
        'is_staff_user': request.user.is_staff or request.user.is_superuser,
    })


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
    if request.user.is_staff or request.user.is_superuser:
        property = get_object_or_404(Property, id=property_id)
    else:
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


@login_required
def delete_property(request, property_id):
    property = get_object_or_404(Property, id=property_id)

    if property.profile != request.user.profile and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to delete this property.')
        return redirect('list_properties')

    if request.method == 'POST':
        property.delete()
        messages.success(request, 'Property deleted successfully.')
        return redirect('list_properties')

    return render(request, 'accounts/property_confirm_delete.html', {'property': property})