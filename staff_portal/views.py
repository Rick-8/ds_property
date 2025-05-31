from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from staff_portal.models import Route
from .models import Job, Route
import json


def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


@login_required
def staff_dashboard(request):
    context = {}

    if request.user.is_superuser:
        unassigned_jobs = Job.objects.filter(route__isnull=True).order_by('scheduled_date')
        context['unassigned_jobs'] = unassigned_jobs
        context['routes'] = Route.objects.all()
    else:
        assigned_jobs = Job.objects.filter(
            route__in=request.user.routes.all()
        ).order_by('scheduled_date')
        context['assigned_jobs'] = assigned_jobs

    return render(request, 'staff_portal/dashboard.html', context)


def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk)
    return render(request, 'staff_portal/job_detail.html', {'job': job})


@login_required
def mark_job_complete(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if request.method == "POST":
        job.status = 'complete'
        job.save()
        messages.success(request, "Job marked as complete.")
    return redirect('staff_portal:job_detail', job_id=job.id)


@superuser_required
@login_required
def assign_job_route(request, job_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            route_id = data.get('route_id')
            job = Job.objects.get(id=job_id)
            route = Route.objects.get(id=route_id)
            job.route = route
            job.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return HttpResponseBadRequest('Invalid request method')
