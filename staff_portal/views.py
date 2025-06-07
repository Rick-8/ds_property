from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.contrib import messages
from django.db.models import Q
from datetime import date, timedelta, datetime
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from .models import JobFeedback
from .forms import JobFeedbackForm
from django.utils.timezone import now
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.db.models import Prefetch
from django.utils.timezone import localdate
from django.contrib.auth import authenticate
from django.views.decorators.http import require_POST
from memberships.models import ServiceAgreement

import json
import logging
from django import forms

from staff_portal.models import Job, Route, StaffRouteAssignment
from accounts.models import Property


logger = logging.getLogger(__name__)


def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


@login_required
def staff_dashboard(request):
    context = {}
    if request.user.is_superuser:
        unassigned_jobs = Job.objects.select_related('property').filter(route__isnull=True).order_by('scheduled_date')
        routes = Route.objects.all()

        context['unassigned_jobs'] = unassigned_jobs  # Pass full objects, not dicts
        context['routes'] = routes
    else:
        assigned_jobs = Job.objects.filter(
            Q(route__in=request.user.routes.all()) | Q(assigned_staff=request.user)
        ).order_by('scheduled_date')
        context['assigned_jobs'] = assigned_jobs

    return render(request, 'staff_portal/dashboard.html', context)


@login_required
def job_detail(request, pk):
    job = get_object_or_404(Job.objects.select_related('property').prefetch_related('assigned_staff'), pk=pk)

    if not (request.user.is_superuser or request.user in job.assigned_staff.all()):
        return HttpResponseForbidden("You cannot leave feedback on this job.")

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
        'job_display_id': f"J{job.id}",
        'property_display_id': f"P{job.property.id}",
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

        # Re-fetch the service agreement to check its current active status
        if job.service_agreement:
            fresh_agreement = ServiceAgreement.objects.filter(
                id=job.service_agreement.id,
                active=True
            ).first()

            if fresh_agreement:
                Job.objects.create(
                    title=job.title,
                    description=job.description,
                    property=job.property,
                    service_agreement=fresh_agreement,
                    scheduled_date=job.scheduled_date + timedelta(weeks=1),
                    status="PENDING",
                )

    return redirect("/staff/jobs/staff/")


@login_required
@superuser_required
def assign_job_route(request, job_id):
    """
    Assign a route to a job and link the appropriate staff member based on the route and job's scheduled date.

    This view:
    - Accepts a POST request with a JSON payload containing 'route_id'.
    - Sets the route for the specified job.
    - Uses the job's existing scheduled_date.
    - Finds a matching StaffRouteAssignment for the same route and scheduled date.
    - If found, assigns the staff to the job.

    Returns:
        JsonResponse indicating success or failure.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            route_id = data.get('route_id')
            scheduled_date_str = data.get('scheduled_date')

            job = Job.objects.get(id=job_id)
            route = Route.objects.get(id=route_id)

            # Update route
            job.route = route

            # Update scheduled date if provided
            if scheduled_date_str:
                try:
                    scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d').date()
                    job.scheduled_date = scheduled_date
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD'})

            # Auto-assign staff based on the new route/date
            staff_assignment = StaffRouteAssignment.objects.filter(
                route=route,
                start_date=job.scheduled_date,
                end_date=job.scheduled_date
            ).first()

            if staff_assignment:
                job.assigned_staff.set([staff_assignment.staff])

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
    valid_jobs = Job.objects.filter(
        status="COMPLETED",
        property__isnull=False,
        title__isnull=False
    ).select_related('property').order_by('-completed_date')

    jobs = [
        {
            "job": job,
            "display_id": f"J{job.id}",
            "property_display_id": f"P{job.property.id}"
        }
        for job in valid_jobs
    ]

    return render(request, 'staff_portal/completed_jobs.html', {'jobs': jobs})


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
            # Extract all keys starting with 'assignment_' from POST
            current_keys = set(k for k in request.POST if k.startswith('assignment_'))
            # Extract all unique dates from keys
            dates = {k.split('_')[1] for k in current_keys}
            # Find the earliest and latest dates for the range
            start_date = min(datetime.strptime(d, '%Y-%m-%d').date() for d in dates)
            end_date = max(datetime.strptime(d, '%Y-%m-%d').date() for d in dates)
            assignments_to_keep = []

            # Loop through POST items and update/create/delete assignments
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

            # Delete assignments outside the current range that are not kept
            StaffRouteAssignment.objects.filter(
                start_date__gte=start_date,
                end_date__lte=end_date
            ).exclude(id__in=assignments_to_keep).delete()

            # New: Assign staff to jobs based on route and date assignments
            assignments = StaffRouteAssignment.objects.filter(
                start_date__gte=start_date,
                end_date__lte=end_date
            )
            for assignment in assignments:
                # Find jobs matching route and scheduled date
                jobs = Job.objects.filter(
                    route=assignment.route,
                    scheduled_date=assignment.start_date  # Assuming one-day assignments
                )
                for job in jobs:
                    job.assigned_staff.set([assignment.staff])
                    job.save()

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


@login_required
def staff_job_list(request):
    user = request.user
    today = localdate()

    active_routes = StaffRouteAssignment.objects.filter(
        staff=user,
        start_date__lte=today,
        end_date__gte=today
    ).values_list('route', flat=True)

    jobs = Job.objects.filter(
        Q(assigned_staff=user) |
        Q(assigned_staff__isnull=True, route__in=active_routes),
        status__in=["NEW", "PENDING"],
        scheduled_date=today
    ).distinct().order_by('scheduled_date')

    return render(request, 'staff_portal/staff_jobs.html', {'jobs': jobs, 'today': today})


@login_required
@superuser_required
@csrf_exempt
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

                        # Optional: Validate if staff_id and route_id exist in DB
                        from django.contrib.auth import get_user_model
                        User = get_user_model()
                        try:
                            staff_obj = User.objects.get(pk=staff_id)
                        except User.DoesNotExist:
                            logger.error(f"Staff with id {staff_id} does not exist.")
                            return JsonResponse({'success': False, 'error': f'Staff id {staff_id} invalid'}, status=400)

                        # Same for route - assuming Route model
                        from staff_portal.models import Route, StaffRouteAssignment

                        try:
                            route_obj = Route.objects.get(pk=route_id_int)
                        except Route.DoesNotExist:
                            logger.error(f"Route with id {route_id_int} does not exist.")
                            return JsonResponse({'success': False, 'error': f'Route id {route_id_int} invalid'}, status=400)

                        assignment, created = StaffRouteAssignment.objects.update_or_create(
                            route=route_obj,
                            start_date=day_date,
                            end_date=day_date,
                            defaults={'staff': staff_obj}
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
            logger.exception("Error while saving schedule")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


def routes_overview(request):
    routes = Route.objects.prefetch_related(
        Prefetch(
            'job_set',
            queryset=Job.objects.exclude(status='COMPLETED').order_by('scheduled_date'),
            to_attr='active_jobs'
        )
    )
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


@login_required
def missed_jobs_view(request):
    today = now().date()

    missed_jobs = Job.objects.filter(
        scheduled_date=today,
        assigned_staff__isnull=False
    ).exclude(status='COMPLETED').distinct()

    context = {
        'missed_jobs': missed_jobs,
        'today': today,
    }

    return render(request, 'staff_portal/missed_jobs.html', context)


@login_required
def future_jobs(request):
    today = date.today()
    future_jobs = Job.objects.filter(scheduled_date__gt=today).order_by('scheduled_date')
    return render(request, 'staff_portal/future_jobs.html', {'future_jobs': future_jobs})


@csrf_exempt
@login_required
@superuser_required
def assign_job_staff(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            # Example data: {"job_15": 3, "job_18": 2}
            for job_key, staff_id in data.items():
                if job_key.startswith("job_"):
                    job_id = int(job_key.split("_")[1])
                    job = Job.objects.get(id=job_id)
                    if staff_id:
                        staff_user = User.objects.get(id=staff_id)
                        job.assigned_staff.set([staff_user])  # Assign single user
                    else:
                        job.assigned_staff.clear()  # Remove all assignments
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
    return JsonResponse({"success": False, "error": "Invalid request method"}, status=400)


@login_required
def mark_job_missed(request, pk):
    job = get_object_or_404(Job, pk=pk)

    if request.method == "POST":
        feedback_text = request.POST.get("feedback", "").strip()

        if not feedback_text:
            messages.error(request, "Please enter feedback before marking as missed.")
            return redirect("job_detail", pk=job.pk)

        # Append missed job comment with date
        missed_note = f"\n\nMissed job - {timezone.localdate().strftime('%B %d, %Y')}"
        full_feedback = feedback_text + missed_note

        JobFeedback.objects.create(job=job, user=request.user, feedback=full_feedback)

        # Reset job assignment
        job.assigned_staff.clear()
        job.route = None
        job.status = "PENDING"
        job.save()

        messages.success(request, "Job marked as missed and reassigned.")
        return redirect("dashboard")

    return redirect("dashboard")


class RouteCreateView(CreateView):
    model = Route
    fields = ['name', 'description']  # Adjust fields to your model
    template_name = 'staff_portal/route_form.html'
    success_url = reverse_lazy('routes_overview')  # Adjust to your routes overview url name


class RouteUpdateView(UpdateView):
    model = Route
    fields = ['name', 'description']  # Same fields as create
    template_name = 'staff_portal/route_form.html'
    success_url = reverse_lazy('routes_overview')


@login_required
def all_jobs_view(request):
    jobs = Job.objects.all().order_by('-created_at')
    routes = Route.objects.all()
    return render(request, 'staff_portal/all_jobs.html', {'jobs': jobs, 'routes': routes})


@login_required
def delete_job(request, job_id):
    if request.method == 'POST':
        password = request.POST.get('password')
        user = authenticate(username=request.user.username, password=password)
        if user:
            job = get_object_or_404(Job, id=job_id)
            job.delete()
            messages.success(request, "Job deleted successfully.")
        else:
            messages.error(request, "Invalid password. Job not deleted.")
        return redirect('all_jobs')
    return redirect('all_jobs')


@login_required
def delete_all_jobs(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        user = authenticate(username=request.user.username, password=password)
        if user:
            Job.objects.all().delete()
            messages.success(request, "All jobs deleted successfully.")
        else:
            messages.error(request, "Invalid password. No jobs were deleted.")
        return redirect('all_jobs')
    return redirect('all_jobs')


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def reassign_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    job.assigned_staff.clear()
    job.route = None
    job.status = "PENDING"
    job.save()

    messages.success(request, f"Job '{job.title}' has been cleared for reassignment.")
    return redirect('missed_jobs')


class EditJobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['route', 'scheduled_date']
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date'}),
        }


@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.method == 'POST':
        form = EditJobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated successfully.")
            return redirect('all_jobs')
    else:
        form = EditJobForm(instance=job)

    return render(request, 'staff_portal/edit_job_modal.html', {'form': form, 'job': job})
