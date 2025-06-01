from django.urls import path
from . import views

urlpatterns = [
    path('', views.staff_dashboard, name='dashboard'),

    # Job related views
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/complete/', views.mark_job_complete, name='mark_job_complete'),

    # Assign job to route (superuser only, AJAX)
    path('jobs/<int:job_id>/assign_route/', views.assign_job_route, name='assign_job_route'),

    # Job status views
    path('jobs/status/', views.job_status_overview, name='job_status_overview'),
    path('jobs/status/list/', views.jobs_by_status, name='jobs_by_status'),

    # Completed jobs
    path('jobs/completed/', views.completed_jobs, name='completed_jobs'),

    # Staff jobs list (jobs assigned to logged-in user)
    path('jobs/staff/', views.staff_job_list, name='staff_job_list'),

    # Route management (superuser only)
    path('routes/', views.routes_overview, name='routes_overview'),
    path('routes/jobs/', views.route_job_list, name='route_job_list'),

    # Staff schedule planner (superuser only)
    path('schedule/planner/', views.staff_schedule_planner, name='staff_schedule_planner'),
    path('schedule/save/', views.save_schedule, name='save_schedule'),
]
