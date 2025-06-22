import datetime
from django.contrib.auth import logout


class LogoutStaffAtTenPM:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        now = datetime.datetime.now()
        ten_pm = now.replace(hour=22, minute=0, second=0, microsecond=0)
        session_timestamp = request.session.get('login_time')

        if request.user.is_authenticated and request.user.is_staff:
            if not session_timestamp:
                request.session['login_time'] = now.timestamp()
            else:
                if now >= ten_pm:
                    login_time = datetime.datetime.fromtimestamp(session_timestamp)
                    if login_time < ten_pm:
                        logout(request)
                        request.session.flush()
        response = self.get_response(request)
        return response
