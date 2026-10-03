from django.shortcuts import redirect
from django.urls import reverse

from .models import Profile


class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user

        if not user.is_authenticated:
            return self.get_response(request)

        password_change_url = reverse('password_change')
        logout_url = reverse('logout')

        if request.path in {
            password_change_url,
            logout_url,
        }:
            return self.get_response(request)

        profile, _ = Profile.objects.get_or_create(
            user=user,
        )

        if profile.must_change_password:
            return redirect('password_change')

        return self.get_response(request)