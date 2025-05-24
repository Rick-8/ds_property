from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from .models import ServicePackage
from .forms import ServicePackageForm


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
        return redirect('list')
    return render(request, 'memberships/confirm_delete.html', {'package': package})
