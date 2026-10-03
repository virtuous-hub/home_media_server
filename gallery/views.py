import os
import shutil
import uuid
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.static import serve as django_static_serve
from PIL import Image, UnidentifiedImageError

from .models import Profile
from .storage import create_thumbnail, delete_photo_files, get_photo_date


def _can_manage_private(user):
    if user.is_superuser:
        return True

    profile, _ = Profile.objects.get_or_create(user=user)
    return profile.can_manage_private


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


def _no_store(response):
    response['Cache-Control'] = (
        'private, no-store, no-cache, must-revalidate'
    )
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@login_required
def authenticated_media(request, path):
    """
    Отдаёт только обычный MEDIA_ROOT и только после авторизации.
    PRIVATE/INBOX сюда физически не входят: они лежат в protected_media.
    """
    normalized_path = str(path).replace('\\', '/')

    response = django_static_serve(
        request,
        normalized_path,
        document_root=settings.MEDIA_ROOT,
        show_indexes=False,
    )

    # Браузер может хранить обычный медиаконтент, но должен
    # перепроверять доступ при каждом открытии URL.
    response['Cache-Control'] = 'private, no-cache'
    return response


class HomePasswordChangeView(PasswordChangeView):
    template_name = 'registration/password_change_form.html'
    success_url = reverse_lazy('password_change_done')

    def form_valid(self, form):
        response = super().form_valid(form)

        profile, _ = Profile.objects.get_or_create(
            user=self.request.user,
        )
        profile.must_change_password = False
        profile.save(
            update_fields=['must_change_password'],
        )

        return response


@login_required
def gallery(request):
    if request.method == 'POST':
        photos = request.FILES.getlist('photos')

        if photos:
            can_manage_private = _can_manage_private(
                request.user
            )

            if can_manage_private:
                batch_id = str(uuid.uuid4())

                photo_root = (
                    settings.INBOX_PHOTOS_ROOT
                    / str(request.user.id)
                    / batch_id
                )

                thumbnail_root = (
                    settings.INBOX_THUMBNAILS_ROOT
                    / str(request.user.id)
                    / batch_id
                )

                photo_root.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                thumbnail_root.mkdir(
                    parents=True,
                    exist_ok=True,
                )

            else:
                photo_root = settings.COMMON_PHOTOS_ROOT
                thumbnail_root = settings.COMMON_THUMBNAILS_ROOT

            storage = FileSystemStorage(
                location=photo_root,
            )

            saved_count = 0

            for photo in photos:
                try:
                    image = Image.open(photo)
                    image.verify()
                    photo.seek(0)

                    upload_name = _upload_filename(
                        photo.name
                    )

                    filename = storage.save(
                        upload_name,
                        photo,
                    )

                    create_thumbnail(
                        filename,
                        photo_root,
                        thumbnail_root,
                    )

                    saved_count += 1

                except (UnidentifiedImageError, ValueError):
                    messages.error(
                        request,
                        f'{photo.name} не является изображением',
                    )

            if (
                can_manage_private
                and saved_count > 0
            ):
                return redirect('review_upload')

            return redirect('gallery')

    files = [
        path.name
        for path in settings.COMMON_PHOTOS_ROOT.iterdir()
        if path.is_file()
    ]

    files.sort(
        key=lambda f: os.path.getmtime(
            settings.COMMON_PHOTOS_ROOT / f
        ),
        reverse=True,
    )
    files = files[:3]

    photos = []

    for filename in files:
        photos.append({
            'filename': filename,
            'date': get_photo_date(filename),
        })

    video_files = [
        path.name
        for path in settings.VIDEOS_ROOT.iterdir()
        if path.is_file()
    ]

    video_files.sort(
        key=lambda f: os.path.getmtime(
            settings.VIDEOS_ROOT / f
        ),
        reverse=True,
    )

    video_files = video_files[:3]

    latest_videos = []

    for filename in video_files:
        video_path = Path(filename)

        latest_videos.append({
            'filename': filename,
            'thumbnail': f'{video_path.stem}.jpg',
        })

    return render(
        request,
        'gallery/index.html',
        {
            'photos': photos,
            'latest_videos': latest_videos,
        }
    )


@login_required
def review_upload(request):
    if not _can_manage_private(request.user):
        raise Http404

    user_photo_root = (
        settings.INBOX_PHOTOS_ROOT
        / str(request.user.id)
    )

    user_thumbnail_root = (
        settings.INBOX_THUMBNAILS_ROOT
        / str(request.user.id)
    )

    if not user_photo_root.exists():
        return redirect('gallery')

    photos = []

    for batch_root in user_photo_root.iterdir():
        if not batch_root.is_dir():
            continue

        batch_id = batch_root.name

        for photo_path in batch_root.iterdir():
            if not photo_path.is_file():
                continue

            key = f'{batch_id}|{photo_path.name}'

            photos.append({
                'key': key,
                'filename': photo_path.name,
                'batch_id': batch_id,
                'mtime': photo_path.stat().st_mtime,
            })

    photos.sort(
        key=lambda photo: photo['mtime'],
    )

    if not photos:
        return redirect('gallery')

    if request.method == 'POST':
        private_photos = set(
            request.POST.getlist('private_photos')
        )

        for photo in photos:
            filename = photo['filename']
            batch_id = photo['batch_id']

            source_photo = (
                user_photo_root
                / batch_id
                / filename
            )

            source_thumbnail = (
                user_thumbnail_root
                / batch_id
                / filename
            )

            if photo['key'] in private_photos:
                target_photo_root = (
                    settings.PRIVATE_PHOTOS_ROOT
                )

                target_thumbnail_root = (
                    settings.PRIVATE_THUMBNAILS_ROOT
                )

            else:
                target_photo_root = (
                    settings.COMMON_PHOTOS_ROOT
                )

                target_thumbnail_root = (
                    settings.COMMON_THUMBNAILS_ROOT
                )

            storage = FileSystemStorage(
                location=target_photo_root,
            )

            target_filename = (
                storage.get_available_name(filename)
            )

            shutil.move(
                str(source_photo),
                str(
                    target_photo_root
                    / target_filename
                ),
            )

            if source_thumbnail.exists():
                shutil.move(
                    str(source_thumbnail),
                    str(
                        target_thumbnail_root
                        / target_filename
                    ),
                )

        shutil.rmtree(
            user_photo_root,
            ignore_errors=True,
        )

        shutil.rmtree(
            user_thumbnail_root,
            ignore_errors=True,
        )

        messages.success(
            request,
            'Фотографии распределены.',
        )

        return redirect('gallery')

    return render(
        request,
        'gallery/review_upload.html',
        {
            'photos': photos,
        },
    )


@login_required
def inbox_thumbnail(request, batch_id, filename):
    if not _can_manage_private(request.user):
        raise Http404

    safe_filename = _safe_filename(filename)

    thumbnail_path = (
        settings.INBOX_THUMBNAILS_ROOT
        / str(request.user.id)
        / str(batch_id)
        / safe_filename
    )

    if (
        not thumbnail_path.exists()
        or not thumbnail_path.is_file()
    ):
        raise Http404

    response = FileResponse(
        open(thumbnail_path, 'rb'),
    )

    return _no_store(response)


@login_required
def all_photos(request):
    files = [
        path.name
        for path in settings.COMMON_PHOTOS_ROOT.iterdir()
        if path.is_file()
    ]

    photos = []

    for filename in files:
        photos.append({
            'filename': filename,
            'date': get_photo_date(filename),
        })

    photos.sort(
        key=lambda photo: photo['date'],
        reverse=True,
    )

    per_page = request.GET.get('per_page', 20)

    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 20

    per_page = max(1, min(per_page, 100))

    paginator = Paginator(photos, per_page)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    return render(
        request,
        'gallery/all_photos.html',
        {'page_obj': page_obj},
    )


@login_required
def private_photos(request):
    if not _can_manage_private(request.user):
        raise Http404

    files = [
        path.name
        for path in settings.PRIVATE_PHOTOS_ROOT.iterdir()
        if path.is_file()
    ]

    photos = []

    for filename in files:
        photos.append({
            'filename': filename,
            'date': get_photo_date(
                filename,
                settings.PRIVATE_PHOTOS_ROOT,
            ),
        })

    photos.sort(
        key=lambda photo: photo['date'],
        reverse=True,
    )

    per_page = request.GET.get('per_page', 20)

    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 20

    per_page = max(1, min(per_page, 100))

    paginator = Paginator(
        photos,
        per_page,
    )

    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    return render(
        request,
        'gallery/private_photos.html',
        {
            'page_obj': page_obj,
        },
    )


@login_required
def private_thumbnail(request, filename):
    if not _can_manage_private(request.user):
        raise Http404

    safe_filename = _safe_filename(filename)

    thumbnail_path = (
        settings.PRIVATE_THUMBNAILS_ROOT
        / safe_filename
    )

    if (
        not thumbnail_path.exists()
        or not thumbnail_path.is_file()
    ):
        raise Http404

    response = FileResponse(
        open(thumbnail_path, 'rb'),
    )

    return _no_store(response)


@login_required
def private_photo_file(request, filename):
    if not _can_manage_private(request.user):
        raise Http404

    safe_filename = _safe_filename(filename)

    photo_path = (
        settings.PRIVATE_PHOTOS_ROOT
        / safe_filename
    )

    if (
        not photo_path.exists()
        or not photo_path.is_file()
    ):
        raise Http404

    response = FileResponse(
        open(photo_path, 'rb'),
    )

    return _no_store(response)


@login_required
def private_download_photo(request, filename):
    if not _can_manage_private(request.user):
        raise Http404

    safe_filename = _safe_filename(filename)

    photo_path = (
        settings.PRIVATE_PHOTOS_ROOT
        / safe_filename
    )

    if (
        not photo_path.exists()
        or not photo_path.is_file()
    ):
        raise Http404

    response = FileResponse(
        open(photo_path, 'rb'),
        as_attachment=True,
        filename=safe_filename,
    )

    return _no_store(response)


@login_required
def private_delete_photo(request, filename):
    if not _can_manage_private(request.user):
        raise Http404

    if request.method != 'POST':
        return redirect('private_photos')

    safe_filename = _safe_filename(filename)

    delete_photo_files(
        safe_filename,
        settings.PRIVATE_PHOTOS_ROOT,
        settings.PRIVATE_THUMBNAILS_ROOT,
    )

    return redirect(
        _safe_next_url(request, '/private/')
    )


@login_required
def private_delete_selected_photos(request):
    if not _can_manage_private(request.user):
        raise Http404

    if request.method != 'POST':
        return redirect('private_photos')

    filenames = request.POST.getlist('photos')

    for filename in filenames:
        try:
            safe_filename = _safe_filename(filename)
        except Http404:
            continue

        delete_photo_files(
            safe_filename,
            settings.PRIVATE_PHOTOS_ROOT,
            settings.PRIVATE_THUMBNAILS_ROOT,
        )

    return redirect('private_photos')


@login_required
def delete_photo(request, filename):
    safe_filename = _safe_filename(filename)

    if request.method == 'POST':
        delete_photo_files(
            safe_filename,
            settings.COMMON_PHOTOS_ROOT,
            settings.COMMON_THUMBNAILS_ROOT,
        )

        return redirect(
            _safe_next_url(request, '/')
        )

    return redirect('gallery')


@login_required
def delete_selected_photos(request):
    if request.method != 'POST':
        return redirect('all_photos')

    filenames = request.POST.getlist('photos')

    for filename in filenames:
        try:
            safe_filename = _safe_filename(filename)
        except Http404:
            continue

        delete_photo_files(
            safe_filename,
            settings.COMMON_PHOTOS_ROOT,
            settings.COMMON_THUMBNAILS_ROOT,
        )

    return redirect('all_photos')


@login_required
def download_photo(request, filename):
    safe_filename = _safe_filename(filename)

    photo_path = (
        settings.COMMON_PHOTOS_ROOT
        / safe_filename
    )

    if (
        not photo_path.exists()
        or not photo_path.is_file()
    ):
        raise Http404

    return FileResponse(
        open(photo_path, 'rb'),
        as_attachment=True,
        filename=safe_filename,
    )
