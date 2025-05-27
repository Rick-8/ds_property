from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from memberships.models import ServiceAgreement
from .models import Profile, Property
from .forms import ProfileForm, PropertyForm


@login_required
def view_profile(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile, user=request.user)
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

            # Add to property list if selected
            if form.cleaned_data.get('add_as_property'):
                exists = Property.objects.filter(
                    profile=profile,
                    address_line_1=profile.default_address_line_1,
                    postcode=profile.default_postcode
                ).exists()
                if not exists:
                    Property.objects.create(
                        profile=profile,
                        label='Default Address',
                        address_line_1=profile.default_address_line_1,
                        address_line_2=profile.default_address_line_2,
                        city=profile.default_city,
                        postcode=profile.default_postcode,
                        country=profile.default_country
                    )

            return redirect('home')
        else:
            messages.error(request, "There were errors in your form. Please correct them.")
    else:
        form = ProfileForm(instance=profile, user=request.user)

    if not profile.profile_completed:
        messages.info(request, "Please complete your profile to get the best experience.")

    return render(request, 'account/profile.html', {'form': form})


@login_required
def list_properties(request):
    # Determine which properties to list based on user role
    if request.user.is_staff or request.user.is_superuser:
        # Staff see all properties, ordered by route number and label
        properties = Property.objects.all().order_by('route_number', 'label')
        user = None  # For staff, no specific user filtering on agreements
    else:
        # Normal users see only their own properties, ordered by label
        properties = request.user.profile.properties.all().order_by('label')
        user = request.user

    # Dictionary to hold property ID as key and active service package name or status as value
    property_packages = {}

    # If we have a regular user, check their active service agreements for each property
    if user:
        for prop in properties:
            try:
                # Try to get exactly one active ServiceAgreement for this user and property
                agreement = ServiceAgreement.objects.get(user=user, property=prop, active=True)
                # If found, map property id to the service package name (converted to string)
                property_packages[prop.id] = str(agreement.service_package)
                print(f"[DEBUG] Active agreement found: Property ID {prop.id} has package '{agreement.service_package}'")
            except ServiceAgreement.DoesNotExist:
                # No active agreement found for this property
                property_packages[prop.id] = "Inactive"
                print(f"[DEBUG] No active agreement for Property ID {prop.id} - marked Inactive")
            except ServiceAgreement.MultipleObjectsReturned:
                # More than one active agreement exists, pick the first or handle as needed
                agreements = ServiceAgreement.objects.filter(user=user, property=prop, active=True)
                first_agreement = agreements.first()
                property_packages[prop.id] = str(first_agreement.service_package)
                print(f"[WARNING] Multiple active agreements for Property ID {prop.id}. Using first: '{first_agreement.service_package}'")
    else:
        # For staff users with all properties, just assign empty string (or you could assign other logic)
        for prop in properties:
            property_packages[prop.id] = ""

    # Render the template with:
    # - properties queryset
    # - property_packages dict to check each property's package status
    # - a flag indicating if current user is staff or superuser
    return render(request, 'account/property_list.html', {
        'properties': properties,
        'property_packages': property_packages,
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
        form = ProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.profile_completed = True
            profile.save()

            if form.cleaned_data.get('add_as_property'):
                exists = Property.objects.filter(
                    profile=profile,
                    address_line_1=profile.default_address_line_1,
                    postcode=profile.default_postcode
                ).exists()
                if not exists:
                    Property.objects.create(
                        profile=profile,
                        label='Default Address',
                        address_line_1=profile.default_address_line_1,
                        address_line_2=profile.default_address_line_2,
                        city=profile.default_city,
                        postcode=profile.default_postcode,
                        country=profile.default_country
                    )

            return redirect('home')
    else:
        form = ProfileForm(instance=profile, user=request.user)
    return render(request, 'account/profile.html', {'form': form})


@login_required
def account_dashboard(request):
    return render(request, 'account/dashboard.html')


@login_required
def user_agreements(request):
    agreements = ServiceAgreement.objects.filter(user=request.user, active=True)
    return render(request, 'memberships/user_agreements.html', {'agreements': agreements})