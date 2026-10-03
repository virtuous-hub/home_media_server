from django.urls import path
from . import views

urlpatterns = [
    path('',views.gallery, name='gallery'),
    path('all_photos/',views.all_photos,name='all_photos'),
    path('delete/<str:filename>/', views.delete_photo, name='delete_photo'),
    path('download/<str:filename>/', views.download_photo, name='download_photo'),
    path('delete-selected/', views.delete_selected_photos, name='delete_selected_photos'),
    path('review/',views.review_upload,name='review_upload',),
    path('review/<uuid:batch_id>/thumbnail/<str:filename>/',views.inbox_thumbnail,name='inbox_thumbnail',),
    path('private/', views.private_photos,name='private_photos',),
    path('private/thumbnail/<str:filename>/',views.private_thumbnail,name='private_thumbnail',),
    path('private/photo/<str:filename>/',views.private_photo_file,name='private_photo_file',),
    path('private/download/<str:filename>/',views.private_download_photo,name='private_download_photo',),
    path('private/delete/<str:filename>/',views.private_delete_photo,name='private_delete_photo',),
    path('private/delete-selected/',views.private_delete_selected_photos,name='private_delete_selected_photos',),
]