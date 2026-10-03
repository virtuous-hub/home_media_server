import subprocess
import imageio_ffmpeg
from django.conf import settings
from pathlib import Path


def ensure_video_directories():
    settings.VIDEOS_ROOT.mkdir(
        parents=True,
        exist_ok=True
    )
    settings.VIDEO_THUMBNAILS_ROOT.mkdir(
        parents=True,
        exist_ok=True
    )


def create_video_thumbnail(filename):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    video_path = settings.VIDEOS_ROOT / filename
    thumbnail_name = f'{video_path.stem}.jpg'
    thumbnail_path = settings.VIDEO_THUMBNAILS_ROOT / thumbnail_name
    subprocess.run(
        [
            ffmpeg,
            '-y',
            '-ss', '00:00:01',
            '-i', str(video_path),
            '-frames:v', '1',
            '-vf', 'scale=640:-2',
            str(thumbnail_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return thumbnail_name


def delete_video_files(filename):
    video_path = settings.VIDEOS_ROOT / filename
    thumbnail_name = f'{Path(filename).stem}.jpg'
    thumbnail_path = settings.VIDEO_THUMBNAILS_ROOT / thumbnail_name

    if video_path.exists() and video_path.is_file():
        video_path.unlink()

    if thumbnail_path.exists() and thumbnail_path.is_file():
        thumbnail_path.unlink()