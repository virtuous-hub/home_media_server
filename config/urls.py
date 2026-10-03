from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from gallery.views import HomePasswordChangeView


urlpatterns = [
    path('videos/', include('videos.urls')),
    path('', include('gallery.urls')),
    path('admin/', admin.site.urls),
    path('accounts/password_change/',HomePasswordChangeView.as_view(),name='password_change',),
    path('accounts/',include('django.contrib.auth.urls'),),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
