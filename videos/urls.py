from django.urls import path

from . import views


urlpatterns = [
    path('', views.videos, name='videos'),
    path('upload/', views.upload_video, name='upload_video'),
    path('delete/<str:filename>/', views.delete_video, name='delete_video'),
    path('download/<str:filename>/', views.download_video, name='download_video'),
path('delete-selected/', views.delete_selected_videos, name='delete_selected_videos'
),
]