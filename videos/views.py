import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .storage import create_video_thumbnail, delete_video_files


ALLOWED_VIDEO_EXTENSIONS = {
    '.mp4',
    '.mov',
    '.mkv',
    '.webm',
    '.avi',
}


def _safe_filename(filename):
    """Строгая проверка имени из URL/POST против path traversal."""
    if not filename:
        raise Http404

    if '/' in filename or '\\' in filename:
        raise Http404

    if filename in {'.', '..'}:
        raise Http404

    return filename


def _upload_filename(filename):
    """Для загрузки оставляем только последнюю часть имени файла."""
    normalized = str(filename).replace('\\', '/')
    safe_name = Path(normalized).name

    if not safe_name or safe_name in {'.', '..'}:
        raise ValueError('Некорректное имя файла')

    return safe_name


def _safe_next_url(request, default):
    next_url = request.POST.get('next')

    if (
        next_url
        and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        )
    ):
        return next_url

    return default


@login_required
def videos(request):
    files = os.listdir(settings.VIDEOS_ROOT)

    files.sort(
        key=lambda f: os.path.getmtime(settings.VIDEOS_ROOT / f),
        reverse=True
    )

    per_page = request.GET.get('per_page', 12)

    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 12

    per_page = max(1, min(per_page, 100))

    videos_list = []

    for filename in files:
        video_path = settings.VIDEOS_ROOT / filename

        if not video_path.is_file():
            continue

        videos_list.append({
            'filename': filename,
            'thumbnail': f'{video_path.stem}.jpg',
            'size': video_path.stat().st_size,
        })

    paginator = Paginator(videos_list, per_page)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'videos/videos.html',
        {'page_obj': page_obj}
    )


@login_required
def upload_video(request):
    if request.method != 'POST':
        return redirect('gallery')

    uploaded_videos = request.FILES.getlist('videos')

    if not uploaded_videos:
        return JsonResponse(
            {
                'success': False,
                'error': 'Видео не передано',
            },
            status=400,
        )

    storage = FileSystemStorage(
        location=settings.VIDEOS_ROOT
    )

    video = uploaded_videos[0]

    try:
        upload_name = _upload_filename(video.name)
    except ValueError:
        return JsonResponse(
            {
                'success': False,
                'error': 'Некорректное имя видео',
            },
            status=400,
        )

    extension = Path(upload_name).suffix.lower()

    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        return JsonResponse(
            {
                'success': False,
                'error': (
                    f'{upload_name} не является '
                    'поддерживаемым видео'
                ),
            },
            status=400,
        )

    filename = None

    try:
        filename = storage.save(upload_name, video)
        create_video_thumbnail(filename)

    except Exception as error:
        if filename:
            storage.delete(filename)

        return JsonResponse(
            {
                'success': False,
                'error': (
                    f'Не удалось обработать {upload_name}: '
                    f'{error}'
                ),
            },
            status=500,
        )

    return JsonResponse(
        {
            'success': True,
            'filename': filename,
        },
        status=200,
    )


@login_required
def delete_video(request, filename):
    safe_filename = _safe_filename(filename)

    if request.method == 'POST':
        delete_video_files(safe_filename)

        return redirect(
            _safe_next_url(request, '/videos/')
        )

    return redirect('videos')


@login_required
def delete_selected_videos(request):
    if request.method != 'POST':
        return redirect('videos')

    filenames = request.POST.getlist('videos')

    for filename in filenames:
        try:
            safe_filename = _safe_filename(filename)
        except Http404:
            continue

        delete_video_files(safe_filename)

    return redirect('videos')


@login_required
def download_video(request, filename):
    safe_filename = _safe_filename(filename)
    video_path = settings.VIDEOS_ROOT / safe_filename

    if not video_path.exists() or not video_path.is_file():
        raise Http404

    return FileResponse(
        open(video_path, 'rb'),
        as_attachment=True,
        filename=safe_filename,
    )
