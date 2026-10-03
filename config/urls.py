from django.contrib import admin
from django.urls import include, path

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
        'accounts/',
        include('django.contrib.auth.urls'),
    ),
]
