from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.urls import reverse

from .models import Profile


class ForcePasswordChangeMiddleware:
    """
    Глобальная защита сайта:
    - анонимному пользователю доступна только страница входа и static;
    - после входа пользователь с временным паролем принудительно
      отправляется на смену пароля.

    Это страховка на случай, если у нового view забудут поставить
    @login_required.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        login_url = reverse('login')

        static_prefix = '/' + settings.STATIC_URL.lstrip('/')

        if not user.is_authenticated:
            if (
                request.path == login_url
                or request.path.startswith(static_prefix)
            ):
                return self.get_response(request)

            return redirect_to_login(
                request.get_full_path(),
                login_url,
            )

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
