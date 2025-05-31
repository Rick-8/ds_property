from django.urls import path
from . import views

app_name = 'staff_portal'

urlpatterns = [
    path('dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('job/<int:pk>/', views.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/complete/', views.mark_job_complete, name='mark_complete'),
    path('assign-job/<int:job_id>/', views.assign_job_route, name='assign_job_route'),

]
