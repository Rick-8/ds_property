from django.urls import path
from . import views

urlpatterns = [
    path("user-panel/", views.user_admin_panel, name="user_admin_panel"),
    path("toggle-staff/<int:user_id>/", views.toggle_staff, name="toggle_staff"),
    path("toggle-superuser/<int:user_id>/", views.toggle_superuser, name="toggle_superuser"),
    path("toggle-active/<int:user_id>/", views.toggle_active, name="toggle_active"),
]
