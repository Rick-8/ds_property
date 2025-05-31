from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Route, Job


@login_required
def staff_dashboard(request):
    user = request.user
    routes = user.routes.all()
    jobs = user.assigned_jobs.filter(status__in=['PENDING', 'IN_PROGRESS']).order_by('scheduled_date')

    context = {
        'routes': routes,
        'jobs': jobs,
    }
    return render(request, 'staff_portal/dashboard.html', context)
