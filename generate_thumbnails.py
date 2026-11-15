
import os
import argparse
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from django.conf import settings
from gallery.storage import create_thumbnail
from videos.storage import create_video_thumbnail


PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".avi", ".webm"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    photo_dir = settings.COMMON_PHOTOS_ROOT
    photo_thumbs = settings.COMMON_THUMBNAILS_ROOT

    video_dir = settings.VIDEOS_ROOT
    video_thumbs = settings.VIDEO_THUMBNAILS_ROOT

    photo_thumbs.mkdir(parents=True, exist_ok=True)
    video_thumbs.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0
    errors = 0
    processed = 0

    with open("thumbnail_errors.log", "a", encoding="utf-8") as log:

        for kind, directory, extensions in [
            ("Фото", photo_dir, PHOTO_EXT),
            ("Видео", video_dir, VIDEO_EXT),
        ]:
            for file in sorted(directory.iterdir()):
                if not file.is_file():
                    continue

                if file.suffix.lower() not in extensions:
                    continue

                if args.limit and processed >= args.limit:
                    break

                processed += 1

                if kind == "Фото":
                    thumbnail = photo_thumbs / file.name
                else:
                    thumbnail = video_thumbs / f"{file.stem}.jpg"

                if thumbnail.is_file() and thumbnail.stat().st_size > 0:
                    skipped += 1
                    continue

                try:
                    if kind == "Фото":
                        create_thumbnail(file.name)
                    else:
                        create_video_thumbnail(file.name)

                    created += 1

                except Exception as exc:
                    errors += 1
                    message = f"{kind}: {file.name}: {exc}"
                    print("ОШИБКА:", message, flush=True)
                    log.write(message + "\n")
                    log.flush()

                if processed % 100 == 0:
                    print(
                        f"Обработано: {processed} | "
                        f"Создано: {created} | "
                        f"Пропущено: {skipped} | "
                        f"Ошибки: {errors}",
                        flush=True,
                    )

            if args.limit and processed >= args.limit:
                break

    print("\n===== ГОТОВО =====")
    print("Обработано:", processed)
    print("Создано:", created)
    print("Уже существовали:", skipped)
    print("Ошибки:", errors)


if __name__ == "__main__":
    main()
