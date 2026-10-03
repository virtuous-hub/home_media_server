from django.apps import AppConfig
from .storage import ensure_media_directories


class GalleryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gallery'

    def ready(self):
        ensure_media_directories()

        from . import signals  # noqa: F401