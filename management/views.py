from functools import wraps
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages

User = get_user_model()

def superuser_required(view_func):
    """
    Decorator that ensures the requesting user is authenticated and is a superuser.
    
    Wraps the view function to:
    - Require user login
    - Check if the user is a superuser
    If either condition fails, access is denied.
    """
    @wraps(view_func)
    @login_required
    @user_passes_test(lambda u: u.is_superuser)
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@superuser_required
def user_admin_panel(request):
    """
    Render the user administration panel listing all users.

    Users are ordered by superuser status, staff status, then email.

    Only accessible by superusers.
    """
    users = User.objects.all().order_by('-is_superuser', '-is_staff', 'email')
    return render(request, "management/user_admin_panel.html", {"users": users})

@superuser_required
def toggle_active(request, user_id):
    """
    Toggle the 'is_active' status of a user by their ID.

    If the user is currently active, this will deactivate them, and vice versa.

    Shows a success message upon change and redirects back to the user admin panel.

    Only accessible by superusers.

    Args:
        request: HttpRequest object.
        user_id: Primary key of the user to toggle active status.
    """
    user = get_object_or_404(User, pk=user_id)
    user.is_active = not user.is_active
    user.save()
    messages.success(request, f"Active status updated for {user.email}")
    return redirect("user_admin_panel")

@superuser_required
def toggle_superuser(request, user_id):
    """
    Toggle the 'is_superuser' status of a user by their ID.

    Promotes or demotes the user to/from superuser status.

    Shows a success message upon change and redirects back to the user admin panel.

    Only accessible by superusers.

    Args:
        request: HttpRequest object.
        user_id: Primary key of the user to toggle superuser status.
    """
    user = get_object_or_404(User, pk=user_id)
    user.is_superuser = not user.is_superuser
    user.save()
    messages.success(request, f"Superuser status updated for {user.email}")
    return redirect("user_admin_panel")

@superuser_required
def toggle_staff(request, user_id):
    """
    Toggle the 'is_staff' status of a user by their ID.

    Grants or removes staff privileges.

    Shows a success message upon change and redirects back to the user admin panel.

    Only accessible by superusers.

    Args:
        request: HttpRequest object.
        user_id: Primary key of the user to toggle staff status.
    """
    user = get_object_or_404(User, pk=user_id)
    user.is_staff = not user.is_staff
    user.save()
    messages.success(request, f"Staff status updated for {user.email}")
    return redirect("user_admin_panel")
