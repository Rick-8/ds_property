from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseBadRequest, HttpResponse
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from .models import ServicePackage
from .forms import ServicePackageForm
from django.http import JsonResponse
from accounts.models import Property
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import stripe


# Set your Stripe secret key here
stripe.api_key = 'your_stripe_secret_key'


def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


def servicepackage_list(request):
    packages = ServicePackage.objects.all()
    category = "Silver"
    return render(request, "memberships/list.html", {
        "packages": packages,
        "category": category,
    })


@superuser_required
def package_create(request):
    if request.method == 'POST':
        form = ServicePackageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('servicepackage_list')

    else:
        form = ServicePackageForm()
    return render(request, 'memberships/form.html', {'form': form, 'title': 'Create Service Package'})


@superuser_required
def package_update(request, pk):
    package = get_object_or_404(ServicePackage, pk=pk)
    if request.method == 'POST':
        form = ServicePackageForm(request.POST, instance=package)
        if form.is_valid():
            form.save()
            return redirect('servicepackage_list')
    else:
        form = ServicePackageForm(instance=package)
    return render(request, 'memberships/form.html', {'form': form, 'title': 'Update Service Package'})


@superuser_required
def package_delete(request, pk):
    package = get_object_or_404(ServicePackage, pk=pk)

    if request.method == 'POST':
        package.delete()
        return redirect('servicepackage_list')

    return render(request, 'memberships/confirm_delete.html', {'package': package})


@login_required
def package_selection(request):
    packages = ServicePackage.objects.filter(is_active=True)
    properties = Property.objects.filter(profile__user=request.user, is_active=True)
    return render(request, 'memberships/package_selection.html', {
        'packages': packages,
        'properties': properties,
    })


@login_required
def select_package(request, package_id):
    if request.method == 'POST':
        package = get_object_or_404(ServicePackage, id=package_id, is_active=True)

        property_id = request.POST.get('property_id')

        selected_packages = request.session.get('selected_packages', {})

        property_obj = None
        if property_id:
            try:
                property_obj = Property.objects.get(id=property_id, profile__user=request.user, is_active=True)
            except Property.DoesNotExist:
                property_obj = None

        selected_packages[package.category] = {
            'id': package.id,
            'name': package.name,
            'category': package.get_category_display(),
            'tier': package.get_tier_display(),
            'price_usd': float(package.price_usd),
            'property_id': property_obj.id if property_obj else None,
            'property_label': property_obj.label if property_obj else '',
            'property_address_summary': property_obj.address_summary if property_obj else '',
        }

        request.session['selected_packages'] = selected_packages
        request.session.modified = True

        # Return JSON success response for AJAX
        return JsonResponse({'success': True, 'package': selected_packages[package.category]})

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


@login_required
def confirm_contract(request, package_id):
    # Get the package
    package = get_object_or_404(ServicePackage, pk=package_id)


    # Get the property id from query params
    property_id = request.GET.get('property_id')

    # Optionally, fetch property details (if you have a Property model)
    property_obj = None
    if property_id:
        property_obj = get_object_or_404(Property, pk=property_id)

    context = {
        'package': package,
        'property': property_obj,
    }
    return render(request, 'memberships/confirm_contract.html', context)


@require_POST
def remove_package(request, package_id):
    selected_packages = request.session.get('selected_packages', {})

    # Find package by package_id and remove it
    to_remove_key = None
    for key, pkg in selected_packages.items():
        if str(pkg['id']) == str(package_id):
            to_remove_key = key
            break

    if to_remove_key:
        del selected_packages[to_remove_key]
        request.session['selected_packages'] = selected_packages
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Package not found'}, status=404)


@login_required
@require_POST
def update_package_property(request, package_id):
    import json
    try:
        data = json.loads(request.body)
        property_id = data.get('property_id')
        selected_packages = request.session.get('selected_packages', {})

        category_key = None
        for category, pkg in selected_packages.items():
            if str(pkg['id']) == str(package_id):
                category_key = category
                break

        if not category_key:
            return JsonResponse({'success': False, 'error': 'Package not found in session'}, status=400)

        if not property_id:
            return JsonResponse({'success': False, 'error': 'No property_id provided'}, status=400)

        try:
            property_id_int = int(property_id)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid property_id'}, status=400)

        try:
            property_obj = Property.objects.get(id=property_id_int, profile__user=request.user, is_active=True)
        except Property.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid property selected'}, status=400)

        selected_packages[category_key]['property_id'] = property_obj.id
        selected_packages[category_key]['property_label'] = property_obj.label
        selected_packages[category_key]['property_address_summary'] = property_obj.address_summary

        request.session['selected_packages'] = selected_packages
        request.session.modified = True

        return JsonResponse({'success': True, 'package': selected_packages[category_key]})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)


@csrf_exempt  # you might want this if called by JS fetch/AJAX from frontend
def create_checkout_session(request):
    if request.method == 'POST':
        try:
            # Example: create a checkout session with a single product price
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': 'Service Package',
                            },
                            'unit_amount': 2000,  # $20.00 in cents
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=request.build_absolute_uri('/memberships/success/'),
                cancel_url=request.build_absolute_uri('/memberships/cancel/'),
            )
            return JsonResponse({'id': checkout_session.id})
        except Exception as e:
            return JsonResponse({'error': str(e)})

    return HttpResponse("Method not allowed", status=405)
