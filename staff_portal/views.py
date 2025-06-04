from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from django.db.models import Q
from datetime import date, timedelta, datetime
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from .models import Job, JobFeedback
from .forms import JobFeedbackForm

import json
import logging

from staff_portal.models import Job, Route, StaffRouteAssignment
from accounts.models import Property


logger = logging.getLogger(__name__)


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
            Q(route__in=request.user.routes.all()) | Q(assigned_staff=request.user)
        ).order_by('scheduled_date')
        context['assigned_jobs'] = assigned_jobs
    return render(request, 'staff_portal/dashboard.html', context)


@login_required
def job_detail(request, pk):
    job = get_object_or_404(Job, pk=pk)

    feedback_instance = JobFeedback.objects.filter(job=job, user=request.user).first()

    if request.method == 'POST':
        form = JobFeedbackForm(request.POST, instance=feedback_instance)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.job = job
            feedback.user = request.user
            feedback.save()
            return redirect('job_detail', pk=job.pk)
    else:
        form = JobFeedbackForm(instance=feedback_instance)

    context = {
        'job': job,
        'form': form,
    }
    return render(request, 'staff_portal/job_detail.html', context)


@staff_member_required
def mark_job_complete(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.method == "POST":

        feedback = request.POST.get("feedback", "").strip()
        if feedback:
            JobFeedback.objects.create(
                job=job,
                user=request.user,
                feedback=feedback,
            )

        job.status = "COMPLETED"
        job.completed_date = timezone.now().date()
        job.save()

        if job.property.has_active_service:
            Job.objects.create(
                title=job.title,
                description=job.description,
                property=job.property,
                service_agreement=job.service_agreement,
                scheduled_date=job.scheduled_date + timedelta(weeks=1),
                status="PENDING",

            )

    return redirect("dashboard")


@login_required
@superuser_required
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


@login_required
@superuser_required
def route_job_list(request):
    routes = Route.objects.prefetch_related('job_set').all()
    return render(request, 'staff_portal/route_job_list.html', {'routes': routes})


@login_required
def job_status_overview(request):
    pending = Job.objects.filter(status='PENDING')
    in_progress = Job.objects.filter(status='IN_PROGRESS')
    missed = Job.objects.filter(status='MISSED')
    return render(request, 'staff_portal/status_overview.html', {
        'pending': pending,
        'in_progress': in_progress,
        'missed': missed
    })


@login_required
def completed_jobs_view(request):
    completed_jobs = Job.objects.filter(status='COMPLETED').order_by('-completed_date')
    return render(request, 'staff_portal/completed_jobs.html', {'completed_jobs': completed_jobs})


@login_required
@superuser_required
def staff_schedule_planner(request):
    today = date.today()
    weeks = []
    for w in range(2):
        start = today + timedelta(days=w*7)
        days = [start + timedelta(days=d) for d in range(7)]
        weeks.append({
            'start': start,
            'end': start + timedelta(days=6),
            'days': days
        })
    routes = Route.objects.all()
    eligible_staff = User.objects.filter(is_staff=True).order_by('first_name', 'last_name')
    assignments = StaffRouteAssignment.objects.filter(
        start_date__range=(weeks[0]['start'], weeks[-1]['end'])
    )
    assignment_lookup = {}
    for a in assignments:
        key = f"{a.start_date.isoformat()}_{a.route_id}"
        assignment_lookup[key] = a.staff_id
    context = {
        'weeks': weeks,
        'routes': routes,
        'eligible_staff': eligible_staff,
        'assignment_lookup': assignment_lookup,
    }
    return render(request, 'staff_portal/Staff-Schedule-Planner.html', context)


@csrf_exempt
@login_required
@superuser_required
def save_schedule(request):
    if request.method == 'POST':
        try:
            current_keys = set(k for k in request.POST if k.startswith('assignment_'))
            dates = {k.split('_')[1] for k in current_keys}
            start_date = min(datetime.strptime(d, '%Y-%m-%d').date() for d in dates)
            end_date = max(datetime.strptime(d, '%Y-%m-%d').date() for d in dates)
            assignments_to_keep = []
            for key, staff_id_str in request.POST.items():
                if key.startswith('assignment_'):
                    _, day, route_id = key.split('_')
                    day_date = datetime.strptime(day, '%Y-%m-%d').date()
                    route_id_int = int(route_id)
                    if staff_id_str:
                        staff_id = int(staff_id_str)
                        assignment, created = StaffRouteAssignment.objects.update_or_create(
                            route_id=route_id_int,
                            start_date=day_date,
                            end_date=day_date,
                            defaults={'staff_id': staff_id}
                        )
                        assignments_to_keep.append(assignment.id)
                    else:
                        StaffRouteAssignment.objects.filter(
                            route_id=route_id_int,
                            start_date=day_date,
                            end_date=day_date
                        ).delete()
            StaffRouteAssignment.objects.filter(
                start_date__gte=start_date,
                end_date__lte=end_date
            ).exclude(id__in=assignments_to_keep).delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


@login_required
def staff_job_list(request):
    user = request.user
    today = date.today()

    active_assignments = StaffRouteAssignment.objects.filter(
        staff=user,
        start_date__lte=today,
        end_date__gte=today
    )
    active_routes = [assignment.route for assignment in active_assignments if assignment.route]

    jobs = Job.objects.filter(
        (
            Q(assigned_staff=user) |
            Q(assigned_staff__isnull=True, route__in=active_routes)
        ),
        status__in=["NEW", "PENDING"]
    ).distinct().order_by('scheduled_date')

    return render(request, 'staff_portal/staff_jobs.html', {'jobs': jobs})


@superuser_required
@login_required
def routes_overview(request):
    routes = Route.objects.prefetch_related('job_set').all()
    return render(request, 'staff_portal/routes_overview.html', {'routes': routes})


@login_required
def jobs_by_status(request):
    statuses = ['PENDING', 'IN_PROGRESS', 'MISSED']
    if request.user.is_superuser:
        jobs = Job.objects.filter(status__in=statuses).order_by('scheduled_date')
    else:
        jobs = Job.objects.filter(
            Q(status__in=statuses),
            Q(route__in=request.user.routes.all()) | Q(assigned_staff=request.user)
        ).distinct().order_by('scheduled_date')
    return render(request, 'staff_portal/jobs_by_status.html', {'jobs': jobs})


@login_required
def completed_jobs(request):
    if request.user.is_superuser:
        jobs = Job.objects.filter(status='COMPLETED').order_by('-completed_date')
    else:
        jobs = Job.objects.filter(
            Q(status='COMPLETED') &
            (Q(route__in=request.user.routes.all()) | Q(assigned_staff=request.user))
        ).distinct().order_by('-completed_date')
    return render(request, 'staff_portal/completed_jobs.html', {'jobs': jobs})


@login_required
def submit_feedback(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if not (request.user.is_superuser or request.user in job.assigned_staff.all()):
        messages.error(request, "You are not authorized to update this job.")
        return redirect('job_detail', job_id)

    if job.status == 'COMPLETED':
        messages.warning(request, "Job is already completed. Feedback cannot be updated.")
        return redirect('job_detail', job_id)

    if request.method == 'POST':
        feedback_text = request.POST.get('staff_feedback', '').strip()
        if feedback_text:
            JobFeedback.objects.create(
                job=job,
                user=request.user,
                feedback=feedback_text
            )
            messages.success(request, "Feedback saved successfully.")
        else:
            messages.error(request, "Feedback cannot be empty.")

    return redirect('job_detail', job_id)
