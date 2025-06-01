from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from django.db.models import Q
from datetime import date, timedelta
from django.contrib.auth.models import User
import json

from django.views.decorators.csrf import csrf_exempt
from staff_portal.models import Job, Route, StaffRouteAssignment
from accounts.models import Property
from datetime import date, timedelta, datetime
import logging

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
    return render(request, 'staff_portal/job_detail.html', {'job': job})


@login_required
def mark_job_complete(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    if request.method == "POST":
        job.status = 'COMPLETED'
        job.completed_date = date.today()
        job.save()
        messages.success(request, "Job marked as complete.")
    return redirect('staff_portal:job_detail', pk=job.id)


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
    for w in range(2):  # Two weeks of data
        start = today + timedelta(days=w*7)
        days = [start + timedelta(days=d) for d in range(7)]
        weeks.append({
            'start': start,
            'end': start + timedelta(days=6),
            'days': days
        })

    # Get all routes
    routes = Route.objects.all()

    # Get all eligible staff users (staff or superuser)
    eligible_staff = User.objects.filter(is_staff=True).order_by('first_name', 'last_name')

    # Get assignments within the displayed date range (2 weeks)
    assignments = StaffRouteAssignment.objects.filter(
        start_date__range=(weeks[0]['start'], weeks[-1]['end'])
    )

    # Build lookup dict for quick access in template
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
            print("POST data received:", request.POST)

            current_keys = set()
            for key, value in request.POST.items():
                if key.startswith('assignment_'):
                    current_keys.add(key)
            print("Current keys found:", current_keys)

            dates = set()
            for key in current_keys:
                _, day, route_id = key.split('_')
                dates.add(day)
            print("Dates extracted:", dates)
            start_date = min(datetime.strptime(d, '%Y-%m-%d').date() for d in dates)
            end_date = max(datetime.strptime(d, '%Y-%m-%d').date() for d in dates)
            print("Date range:", start_date, "to", end_date)

            assignments_to_keep = []

            for key, staff_id_str in request.POST.items():
                if key.startswith('assignment_'):
                    _, day, route_id = key.split('_')
                    day_date = datetime.strptime(day, '%Y-%m-%d').date()
                    route_id_int = int(route_id)
                    print(f"Processing assignment for route {route_id_int} on {day_date} with staff {staff_id_str}")

                    if staff_id_str:
                        staff_id = int(staff_id_str)
                        assignment, created = StaffRouteAssignment.objects.update_or_create(
                            route_id=route_id_int,
                            start_date=day_date,
                            end_date=day_date,
                            defaults={'staff_id': staff_id}
                        )
                        print(f"Assignment {'created' if created else 'updated'}: {assignment.id}")
                        assignments_to_keep.append(assignment.id)
                    else:
                        deleted, _ = StaffRouteAssignment.objects.filter(
                            route_id=route_id_int,
                            start_date=day_date,
                            end_date=day_date
                        ).delete()
                        print(f"Deleted {deleted} assignments for route {route_id_int} on {day_date}")

            deleted_extra, _ = StaffRouteAssignment.objects.filter(
                start_date__gte=start_date,
                end_date__lte=end_date
            ).exclude(id__in=assignments_to_keep).delete()
            print(f"Deleted {deleted_extra} extra assignments not in current POST")

            return JsonResponse({'success': True})
        except Exception as e:
            print("Error saving schedule:", e)
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


@login_required
def staff_job_list(request):
    user = request.user
    user_routes = user.routes.all()
    jobs = Job.objects.filter(
        Q(route__in=user_routes) | Q(assigned_staff=user)
    ).distinct().order_by('scheduled_date')

    logger.debug(f"User: {user}, Routes: {list(user_routes)}, Jobs: {list(jobs)}")

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
