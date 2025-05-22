from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile, Property
from django.shortcuts import render
from .forms import ProfileForm, PropertyForm


@login_required
def view_profile(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)

            required_fields = [
                profile.email,
                profile.phone,
                profile.company_name,
                profile.default_address_line_1,
                profile.default_city,
                profile.default_postcode,
                profile.default_country
            ]

            if all(required_fields):
                profile.profile_completed = True
                messages.success(request, "Thank you, your Profile has updated.")
            else:
                profile.profile_completed = False
                messages.warning(request, "Profile updated, but some fields are missing. Please complete your profile.")

            profile.save()
            return redirect('home')
        else:
            messages.error(request, "There were errors in your form. Please correct them.")
    else:
        form = ProfileForm(instance=profile)

    if not profile.profile_completed:
        messages.info(request, "Please complete your profile to get the best experience.")

    return render(request, 'account/profile.html', {'form': form})


@login_required
def list_properties(request):
    if request.user.is_staff or request.user.is_superuser:
        properties = Property.objects.all().order_by('route_number', 'label')
    else:
        properties = request.user.profile.properties.all().order_by('label')
    return render(request, 'account/property_list.html', {
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
    return render(request, 'account/property_form.html', {'form': form, 'title': 'Add Property'})


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
    return render(request, 'account/property_form.html', {'form': form, 'title': 'Edit Property'})


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

    return render(request, 'account/property_confirm_delete.html', {'property': property})


@login_required
def profile_setup(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            profile.profile_completed = True
            profile.save()
            return redirect('home')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'account/profile.html', {'form': form})


@login_required
def account_dashboard(request):
    return render(request, 'account/dashboard.html')
