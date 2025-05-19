from allauth.account.adapter import DefaultAccountAdapter
from django.shortcuts import resolve_url


class MyAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        user = request.user
        if not user.profile.profile_completed:
            return resolve_url('view_profile')
        return resolve_url('home')
