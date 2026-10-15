from django.contrib import admin
from django.urls import include, path
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
)

from gallery.views import (
    HomePasswordChangeView,
    authenticated_media,
)


urlpatterns = [
    # Обычные фото/видео больше не раздаются напрямую через
    # django.conf.urls.static.static(). Каждый запрос к /media/
    # проходит через авторизацию.
    path(
        'media/<path:path>',
        authenticated_media,
        name='authenticated_media',
    ),

    path('videos/', include('videos.urls')),
    path('', include('gallery.urls')),
    path('admin/', admin.site.urls),

    path(
        'accounts/password_change/',
        HomePasswordChangeView.as_view(),
        name='password_change',
    ),
    path(
        'accounts/login/',
        LoginView.as_view(
            template_name='registration/login.html'
        ),
        name='login',
    ),

    path(
        'accounts/logout/',
        LogoutView.as_view(),
        name='logout',
    ),

    path(
        'accounts/password_change/',
        HomePasswordChangeView.as_view(),
        name='password_change',
    ),

    path(
        'accounts/password_change/done/',
        PasswordChangeDoneView.as_view(
            template_name='registration/password_change_done.html'
        ),
        name='password_change_done',
    ),
]
