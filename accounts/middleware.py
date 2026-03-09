from django.utils import timezone
from django.conf import settings
from django.contrib.auth import logout


class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity')
            if last_activity:
                elapsed = (timezone.now() - timezone.datetime.fromisoformat(last_activity)).seconds
                if elapsed > settings.SESSION_COOKIE_AGE:
                    logout(request)
                    request.session['timeout_message'] = True
            request.session['last_activity'] = timezone.now().isoformat()
        response = self.get_response(request)
        return response
