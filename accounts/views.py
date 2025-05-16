from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Profile, Property
from .forms import ProfileForm, PropertyForm


@login_required
def view_profile(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user.profile)
        if form.is_valid():
            form.save()
    else:
        form = ProfileForm(instance=user.profile)

        if 'user_type' in form.fields and not request.user.is_superuser:
            form.fields['user_type'].disabled = True

    return render(request, 'accounts/profile.html', {'form': form})



@login_required
def list_properties(request):
    properties = request.user.profile.properties.all()
    return render(request, 'accounts/property_list.html', {'properties': properties})


@login_required
def add_property(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            property = form.save(commit=False)
            property.profile = request.user.profile
            property.save()
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
            return redirect('list_properties')
    else:
        form = PropertyForm(instance=property)
    return render(request, 'accounts/property_form.html', {'form': form, 'title': 'Edit Property'})
