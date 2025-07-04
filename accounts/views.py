from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Prefetch
from memberships.models import ServiceAgreement
from .models import Profile, Property, NewsletterSignup
from .forms import ProfileForm, PropertyForm
from .forms import NewsletterQuickSignupForm
from .forms import NewsletterSignupAdminForm


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

            # --- SYNC NewsletterSignup with Profile Consent ---
            # If the user consents, ensure they're on the newsletter list
            if profile.marketing_consent:
                NewsletterSignup.objects.update_or_create(
                    email=profile.email,
                    defaults={'consent': True}
                )
            else:
                # If they remove consent, remove from newsletter list
                NewsletterSignup.objects.filter(email=profile.email).delete()
            # --------------------------------------------------

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
    active_agreements_prefetch = Prefetch(
        'serviceagreement_set',
        queryset=ServiceAgreement.objects.filter(active=True).select_related('service_package'),
        to_attr='active_agreements'
    )

    properties = (
        request.user.profile.properties
        .all()
        .order_by('label')
        .prefetch_related(active_agreements_prefetch)
    )

    return render(request, 'account/property_list.html', {
        'properties': properties,
        'is_staff_user': request.user.is_staff,
    })


@staff_member_required
@user_passes_test(lambda u: u.is_superuser)
def list_all_properties(request):
    """
    Superuser-only view to see and edit all properties with search and filter.
    """
    active_agreements_prefetch = Prefetch(
        'serviceagreement_set',
        queryset=ServiceAgreement.objects.filter(active=True).select_related('service_package'),
        to_attr='active_agreements'
    )

    properties = Property.objects.all().order_by('route_number', 'label').prefetch_related(active_agreements_prefetch)

    search_query = request.GET.get('search', '').strip()
    filter_status = request.GET.get('filter', 'all')

    if search_query:
        properties = properties.filter(
            Q(label__icontains=search_query) |
            Q(address_summary__icontains=search_query)
        )

    if filter_status == 'subscribed':
        properties = properties.filter(active_agreements__isnull=False).distinct()
    elif filter_status == 'not_subscribed':
        properties = properties.filter(active_agreements__isnull=True)

    context = {
        'properties': properties,
        'search_query': search_query,
        'filter_status': filter_status,
    }
    return render(request, 'account/property_list_all.html', context)


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
@user_passes_test(lambda u: u.is_superuser)
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
def property_list(request):
    properties = Property.objects.filter(profile__user=request.user).prefetch_related(
        Prefetch(
            'serviceagreement_set',
            queryset=ServiceAgreement.objects.filter(active=True).select_related('service_package'),
            to_attr='active_agreements'
        )
    )

    context = {
        'properties': properties
    }
    return render(request, 'account/property_list.html', context)


@login_required
def account_dashboard(request):
    return render(request, 'account/dashboard.html')


@login_required
def user_agreements(request):
    agreements = ServiceAgreement.objects.filter(user=request.user, active=True)
    return render(request, 'memberships/user_agreements.html', {'agreements': agreements})


@user_passes_test(lambda u: u.is_superuser)
def admin_property_list(request):
    active_agreements_prefetch = Prefetch(
        'serviceagreement_set',
        queryset=ServiceAgreement.objects.filter(active=True).select_related('service_package'),
        to_attr='active_agreements'
    )

    properties = (
        Property.objects
        .all()
        .order_by('route_number', 'label')
        .prefetch_related(active_agreements_prefetch)
    )

    return render(request, 'admin/property_list.html', {
        'properties': properties,
    })


def newsletter_signup(request):
    if request.method == "POST":
        form = NewsletterQuickSignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            consent = form.cleaned_data['consent']
            signup, created = NewsletterSignup.objects.get_or_create(
                email=email,
                defaults={'consent': consent}
            )
            if not created and signup.consent != consent:
                signup.consent = consent
                signup.save()
            try:
                profile = Profile.objects.get(email=email)
                profile.marketing_consent = consent
                profile.save()
            except Profile.DoesNotExist:
                pass

            messages.success(request, "Thank you for signing up for our newsletter!")
            return redirect('newsletter_signup')
    else:
        form = NewsletterQuickSignupForm()
    return render(request, "account/newsletter_signup.html", {"form": form})


@staff_member_required
def newsletter_crud_list(request):
    signups = NewsletterSignup.objects.all().order_by('-date_joined')
    return render(request, 'account/newsletter_crud_list.html', {'signups': signups})


@staff_member_required
def newsletter_crud_edit(request, pk):
    signup = get_object_or_404(NewsletterSignup, pk=pk)
    if request.method == "POST":
        form = NewsletterSignupAdminForm(request.POST, instance=signup)
        if form.is_valid():
            form.save()

            try:
                profile = Profile.objects.get(email=signup.email)
                profile.marketing_consent = signup.consent
                profile.save()
            except Profile.DoesNotExist:
                pass

            messages.success(request, "Signup updated.")
            return redirect('newsletter_crud_dashboard')
    else:
        form = NewsletterSignupAdminForm(instance=signup)
    return render(request, 'account/newsletter_crud_edit.html', {'form': form, 'signup': signup})


@staff_member_required
def newsletter_crud_delete(request, pk):
    signup = get_object_or_404(NewsletterSignup, pk=pk)
    if request.method == "POST":

        try:
            profile = Profile.objects.get(email=signup.email)
            profile.marketing_consent = False
            profile.save()
        except Profile.DoesNotExist:
            pass

        signup.delete()
        messages.success(request, "Signup deleted and user consent revoked (if user exists).")
        return redirect('newsletter_crud_dashboard')
    return render(request, 'account/newsletter_crud_confirm_delete.html', {'signup': signup})


@staff_member_required
def newsletter_crud_dashboard(request):
    search_query = request.GET.get('q', '').strip()
    signups = NewsletterSignup.objects.all().order_by('-date_joined')
    if search_query:
        signups = signups.filter(email__icontains=search_query)
    return render(request, 'account/newsletter_crud_dashboard.html', {
        'signups': signups,
        'search_query': search_query
    })
