from django.urls import path
from . import views

urlpatterns = [
    path('', views.staff_dashboard, name='dashboard'),

    # Job related views
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/complete/', views.mark_job_complete, name='mark_job_complete'),
    path('jobs/delete/<int:job_id>/', views.delete_job, name='delete_job'),
    path('jobs/delete_all/', views.delete_all_jobs, name='delete_all_jobs'),
    path('my-jobs/', views.staff_job_list, name='my_jobs'),

    # Assign job to route (superuser only, AJAX)
    path('jobs/<int:job_id>/assign_route/', views.assign_job_route, name='assign_job_route'),
    path('assign_job_staff/', views.assign_job_staff, name='assign_job_staff'),
    path('routes/add/', views.RouteCreateView.as_view(), name='route_add'),
    path('routes/<int:pk>/edit/', views.RouteUpdateView.as_view(), name='route_edit'),
    path('jobs/<int:job_id>/edit/', views.edit_job, name='edit_job'),


    # Job status views
    path('jobs/status/', views.job_status_overview, name='job_status_overview'),
    path('jobs/status/list/', views.jobs_by_status, name='jobs_by_status'),

    # Completed jobs
    path('jobs/completed/', views.completed_jobs, name='completed_jobs'),
    path('jobs/all/', views.all_jobs_view, name='all_jobs'),

    # Staff jobs list (jobs assigned to logged-in user)
    path('jobs/staff/', views.staff_job_list, name='staff_job_list'),
    path('jobs/<int:job_id>/feedback/', views.submit_feedback, name='submit_feedback'),
    path('future-jobs/', views.future_jobs, name='future_jobs'),
    path('jobs/<int:job_id>/reassign/', views.reassign_job, name='reassign_job'),

    # Route management (superuser only)
    path('routes/', views.routes_overview, name='routes_overview'),
    path('routes/jobs/', views.route_job_list, name='route_job_list'),
    path('missed-jobs/', views.missed_jobs_view, name='missed_jobs'),
    path('jobs/<int:pk>/mark-missed/', views.mark_job_missed, name='mark_job_missed'),

    # Staff schedule planner (superuser only)
    path('schedule/planner/', views.staff_schedule_planner, name='staff_schedule_planner'),
    path('schedule/save/', views.save_schedule, name='save_schedule'),
    path('assign_job_route/<int:job_id>/', views.assign_job_route, name='assign_job_route'),
]
