from datetime import datetime

from django.conf import settings
from PIL import Image


def ensure_media_directories():
    directories = [
        settings.PHOTOS_ROOT,
        settings.THUMBNAILS_ROOT,

        settings.COMMON_PHOTOS_ROOT,
        settings.COMMON_THUMBNAILS_ROOT,

        settings.PRIVATE_PHOTOS_ROOT,
        settings.PRIVATE_THUMBNAILS_ROOT,

        settings.INBOX_PHOTOS_ROOT,
        settings.INBOX_THUMBNAILS_ROOT,

        settings.VIDEOS_ROOT,
        settings.VIDEO_THUMBNAILS_ROOT,
    ]

    for directory in directories:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


def create_thumbnail(
    filename,
    photo_root=None,
    thumbnail_root=None,
):
    if photo_root is None:
        photo_root = settings.COMMON_PHOTOS_ROOT

    if thumbnail_root is None:
        thumbnail_root = settings.COMMON_THUMBNAILS_ROOT

    thumbnail_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    photo_path = photo_root / filename
    thumbnail_path = thumbnail_root / filename

    with Image.open(photo_path) as image:
        image.thumbnail((400, 400))
        image.save(thumbnail_path)


def delete_photo_files(
    filename,
    photo_root=None,
    thumbnail_root=None,
):
    if photo_root is None:
        photo_root = settings.COMMON_PHOTOS_ROOT

    if thumbnail_root is None:
        thumbnail_root = settings.COMMON_THUMBNAILS_ROOT

    photo_path = photo_root / filename
    thumbnail_path = thumbnail_root / filename

    if photo_path.exists() and photo_path.is_file():
        photo_path.unlink()

    if (
        thumbnail_path.exists()
        and thumbnail_path.is_file()
    ):
        thumbnail_path.unlink()


def get_photo_date(
    filename,
    photo_root=None,
):
    if photo_root is None:
        photo_root = settings.COMMON_PHOTOS_ROOT

    photo_path = photo_root / filename

    try:
        with Image.open(photo_path) as image:
            exif = image.getexif()
            date_taken = exif.get(36867)

            if date_taken:
                return datetime.strptime(
                    date_taken,
                    '%Y:%m:%d %H:%M:%S',
                )

    except (OSError, ValueError):
        pass

    return datetime.fromtimestamp(
        photo_path.stat().st_mtime
    )