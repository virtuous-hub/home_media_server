document.addEventListener('DOMContentLoaded', function () {

    // =========================================================
    // МЕНЮ НАСТРОЕК
    // =========================================================

    const settingsButton = document.getElementById(
        'settings-button'
    );

    const settingsDropdown = document.getElementById(
        'settings-dropdown'
    );

    if (settingsButton && settingsDropdown) {
        settingsButton.addEventListener('click', function (event) {
            event.stopPropagation();

            settingsDropdown.classList.toggle('hidden');
        });

        settingsDropdown.addEventListener('click', function (event) {
            event.stopPropagation();
        });

        document.addEventListener('click', function () {
            settingsDropdown.classList.add('hidden');
        });
    }

    // =========================================================
    // ЗАГРУЗКА ФОТОГРАФИЙ
    // =========================================================

    const photoInput = document.getElementById('photo-input');
    const uploadForm = document.getElementById('upload-form');

    if (photoInput && uploadForm) {
        photoInput.addEventListener('change', function () {
            if (photoInput.files.length > 0) {
                uploadForm.submit();
            }
        });
    }


    // =========================================================
    // ЗАГРУЗКА ВИДЕО
    // =========================================================

    const videoInput = document.getElementById('video-input');
    const videoUploadForm = document.getElementById(
        'video-upload-form'
    );

    const videoProgress = document.getElementById(
        'video-upload-progress'
    );

    const videoProgressText = document.querySelector(
        '.video-upload-status-text'
    );

    if (videoProgress) {
        videoProgress.classList.add('hidden');
    }

    if (videoInput && videoUploadForm) {
        videoInput.addEventListener(
            'change',
            async function () {
                const videos = Array.from(videoInput.files);

                if (videos.length === 0) {
                    return;
                }

                if (videoProgress) {
                    videoProgress.classList.remove('hidden');
                }

                const failedVideos = [];

                for (let index = 0; index < videos.length; index++) {
                    const video = videos[index];

                    if (videoProgressText) {
                        videoProgressText.textContent =
                            `Загрузка видео ${index + 1} из ${videos.length}...`;
                    }

                    try {
                        await uploadSingleVideo(video);
                    } catch (error) {
                        console.error(
                            'Ошибка загрузки:',
                            video.name,
                            error
                        );

                        failedVideos.push(video.name);
                    }
                }

                if (failedVideos.length === 0) {
                    if (videoProgressText) {
                        videoProgressText.textContent =
                            'Видео загружены';
                    }

                    window.location.href = '/';
                    return;
                }

                if (videoProgress) {
                    videoProgress.classList.add('hidden');
                }

                alert(
                    'Не удалось загрузить:\n\n' +
                    failedVideos.join('\n')
                );

                window.location.href = '/';
            }
        );
    }


    function uploadSingleVideo(video) {
        return new Promise(function (resolve, reject) {
            const formData = new FormData();

            formData.append('videos', video);

            const csrfToken = document.querySelector(
                '[name=csrfmiddlewaretoken]'
            );

            if (csrfToken) {
                formData.append(
                    'csrfmiddlewaretoken',
                    csrfToken.value
                );
            }

            const xhr = new XMLHttpRequest();

            xhr.open(
                'POST',
                videoUploadForm.action,
                true
            );

            xhr.addEventListener('load', function () {
                if (xhr.status >= 200 && xhr.status < 400) {
                    resolve();
                    return;
                }

                reject(
                    new Error(
                        `HTTP ${xhr.status}`
                    )
                );
            });

            xhr.addEventListener('error', function () {
                reject(
                    new Error(
                        'Ошибка соединения'
                    )
                );
            });

            xhr.addEventListener('abort', function () {
                reject(
                    new Error(
                        'Загрузка отменена'
                    )
                );
            });

            xhr.addEventListener('timeout', function () {
                reject(
                    new Error(
                        'Истёк таймаут загрузки'
                    )
                );
            });

            xhr.send(formData);
        });
    }


    // =========================================================
    // ПРОСМОТР ВИДЕО
    // =========================================================

    const videoModal = document.getElementById('video-modal');
    const modalVideo = document.getElementById('modal-video');

    const videoDownloadButton = document.getElementById(
        'video-download-button'
    );

    const videoDeleteForm = document.getElementById(
        'video-delete-form'
    );

    window.openVideo = function (url, filename) {
        if (!videoModal || !modalVideo) {
            return;
        }

        modalVideo.src = url;
        videoModal.classList.add('active');

        if (videoDownloadButton) {
            videoDownloadButton.href =
                '/videos/download/' +
                encodeURIComponent(filename) +
                '/';
        }

        if (videoDeleteForm) {
            videoDeleteForm.action =
                '/videos/delete/' +
                encodeURIComponent(filename) +
                '/';
        }

        modalVideo.play();
    };

    window.closeVideo = function () {
        if (!videoModal || !modalVideo) {
            return;
        }

        modalVideo.pause();
        modalVideo.removeAttribute('src');
        modalVideo.load();

        videoModal.classList.remove('active');
    };

    if (videoDeleteForm) {
        videoDeleteForm.addEventListener(
            'submit',
            function (event) {
                const confirmed = confirm(
                    'Вы действительно хотите удалить это видео?'
                );

                if (!confirmed) {
                    event.preventDefault();
                }
            }
        );
    }

    if (videoModal) {
        videoModal.addEventListener('click', function (event) {
            if (event.target === videoModal) {
                closeVideo();
            }
        });
    }

    // =========================================================
    // МНОЖЕСТВЕННЫЙ ВЫБОР ВИДЕО
    // =========================================================

    const videoSelectModeButton = document.getElementById(
        'video-select-mode-button'
    );

    const videoBulkActions = document.getElementById(
        'video-bulk-actions'
    );

    const videoSelectedCount = document.getElementById(
        'video-selected-count'
    );

    const downloadSelectedVideosButton = document.getElementById(
        'download-selected-videos'
    );

    const deleteSelectedVideosButton = document.getElementById(
        'delete-selected-videos'
    );

    const cancelVideoSelection = document.getElementById(
        'cancel-video-selection'
    );


    const savedVideoSelection = JSON.parse(
        sessionStorage.getItem('selectedVideos') || '[]'
    );

    const selectedVideos = new Set(savedVideoSelection);

    const savedVideoSizes = JSON.parse(
        sessionStorage.getItem('selectedVideoSizes') || '{}'
    );

    const selectedVideoSizes = savedVideoSizes;

    let videoSelectionMode = false;


    function saveVideoSelection() {
        sessionStorage.setItem(
            'selectedVideos',
            JSON.stringify(Array.from(selectedVideos))
        );

        sessionStorage.setItem(
            'selectedVideoSizes',
            JSON.stringify(selectedVideoSizes)
        );
    }


    function updateVideoSelectionUI() {
        if (videoSelectedCount) {
            videoSelectedCount.textContent =
                `Выбрано: ${selectedVideos.size}`;
        }

        if (videoBulkActions) {
            videoBulkActions.classList.toggle(
                'hidden',
                !videoSelectionMode
            );
        }

        document
            .querySelectorAll('.video-card[data-filename]')
            .forEach(function (video) {
                const filename = video.dataset.filename;

                video.classList.toggle(
                    'selected',
                    selectedVideos.has(filename)
                );
            });
    }

    if (downloadSelectedVideosButton) {
        downloadSelectedVideosButton.addEventListener(
            'click',
            async function () {
                if (selectedVideos.size === 0) {
                    return;
                }
                if (selectedVideos.size > 5) {
                    alert(
                        'Можно скачать не более 5 видео за один раз.'
                    );

                    return;
                }

                const maxTotalSize =
                    1024 * 1024 * 1024;

                let totalSize = 0;

                selectedVideos.forEach(function (filename) {
                    totalSize +=
                        selectedVideoSizes[filename] || 0;
                });

                if (totalSize > maxTotalSize) {
                    const totalSizeGb = (
                        totalSize /
                        1024 /
                        1024 /
                        1024
                    ).toFixed(2);

                    alert(
                        `Выбранные видео весят ${totalSizeGb} ГБ. ` +
                        'Максимум для одной загрузки — 1 ГБ.'
                    );

                    return;
                }

                const files = [];

                try {
                    for (const filename of selectedVideos) {
                        const response = await fetch(
                            '/media/videos/' +
                            encodeURIComponent(filename)
                        );

                        if (!response.ok) {
                            continue;
                        }

                        const blob = await response.blob();

                        const file = new File(
                            [blob],
                            filename,
                            {
                                type: blob.type || 'video/mp4'
                            }
                        );

                        files.push(file);
                    }

                    if (files.length === 0) {
                        alert('Не удалось получить видео');
                        return;
                    }

                    if (
                        navigator.canShare &&
                        navigator.canShare({ files: files }) &&
                        navigator.share
                    ) {
                        await navigator.share({
                            files: files
                        });
                        videoSelectionMode = false;
                        clearVideoSelection();

                        if (videoSelectModeButton) {
                            videoSelectModeButton.classList.remove('hidden');
                        }


                        return;
                    }

                    downloadFilesNormally(files);
                    videoSelectionMode = false;
                    clearVideoSelection();

                    if (videoSelectModeButton) {
                        videoSelectModeButton.classList.remove('hidden');
                    }
                    } catch (error) {
                        console.error(error);

                        alert(
                            'Не удалось подготовить видео'
                    );
                }
            }
        );
    }


    function clearVideoSelection() {
        selectedVideos.clear();

        sessionStorage.removeItem('selectedVideos');
        sessionStorage.removeItem('selectedVideoSizes');

        document
            .querySelectorAll('.video-card.selected')
            .forEach(function (video) {
                video.classList.remove('selected');
            });

        updateVideoSelectionUI();
    }


    window.handleVideoClick = function (videoElement) {
        if (!videoSelectionMode) {
            window.openVideo(
                videoElement.dataset.videoUrl,
                videoElement.dataset.filename
            );

            return;
        }

        const filename = videoElement.dataset.filename;

        const size = Number(
            videoElement.dataset.size
        );

        if (!filename || !Number.isFinite(size)) {
            return;
        }

        if (selectedVideos.has(filename)) {
            selectedVideos.delete(filename);

            delete selectedVideoSizes[filename];

            videoElement.classList.remove('selected');
        } else {
            if (selectedVideos.size >= 5) {
                alert(
                    'Можно выбрать не более 5 видео.'
                );

                return;
            }

            selectedVideos.add(filename);

            selectedVideoSizes[filename] = size;

            videoElement.classList.add('selected');
        }

        saveVideoSelection();
        updateVideoSelectionUI();
    };


    if (videoSelectModeButton) {
        videoSelectModeButton.addEventListener(
            'click',
            function () {
                videoSelectionMode = true;

                videoSelectModeButton.classList.add('hidden');

                updateVideoSelectionUI();
            }
        );
    }


    if (cancelVideoSelection) {
        cancelVideoSelection.addEventListener(
            'click',
            function () {
                videoSelectionMode = false;

                clearVideoSelection();

                if (videoSelectModeButton) {
                    videoSelectModeButton.classList.remove(
                        'hidden'
                    );
                }
            }
        );
    }


    if (selectedVideos.size > 0) {
        videoSelectionMode = true;

        if (videoSelectModeButton) {
            videoSelectModeButton.classList.add('hidden');
        }
    }

    updateVideoSelectionUI();

    if (deleteSelectedVideosButton) {
        deleteSelectedVideosButton.addEventListener(
            'click',
            function () {
                if (selectedVideos.size === 0) {
                    return;
                }

                const confirmed = confirm(
                    `Удалить выбранные видео: ${selectedVideos.size} шт.?`
                );

                if (!confirmed) {
                    return;
                }

                const form = document.createElement('form');

                form.method = 'POST';
                form.action = '/videos/delete-selected/';

                const csrfToken = document.querySelector(
                    '[name=csrfmiddlewaretoken]'
                );

                if (csrfToken) {
                    const csrfInput = document.createElement('input');

                    csrfInput.type = 'hidden';
                    csrfInput.name = 'csrfmiddlewaretoken';
                    csrfInput.value = csrfToken.value;

                    form.appendChild(csrfInput);
                }

                selectedVideos.forEach(function (filename) {
                    const input = document.createElement('input');

                    input.type = 'hidden';
                    input.name = 'videos';
                    input.value = filename;

                    form.appendChild(input);
                });

                document.body.appendChild(form);

                sessionStorage.removeItem('selectedVideos');
                sessionStorage.removeItem('selectedVideoSizes');

                form.submit();
            }
        );
    }


    // =========================================================
    // ПРОСМОТР ФОТОГРАФИЙ
    // =========================================================

    const modal = document.getElementById('photo-modal');
    const modalImage = document.getElementById('modal-image');
    const photoDate = document.getElementById('photo-date');
    const deleteForm = document.getElementById('delete-form');
    const deleteNext = document.getElementById('delete-next');
    const downloadButton = document.getElementById(
        'download-button'
    );

    const photoPrev = document.getElementById('photo-prev');
    const photoNext = document.getElementById('photo-next');

    const galleryPhotos = Array.from(
        document.querySelectorAll(
            '.photo[data-photo-url]'
        )
    );

    let currentPhotoIndex = 0;

    function showPhoto(index) {
        const photo = galleryPhotos[index];

        if (!photo || !modal || !modalImage) {
            return;
        }

        const url = photo.dataset.photoUrl;
        const filename = photo.dataset.filename;
        const date = photo.dataset.date;

        modalImage.src = url;
        modal.classList.add('active');

        if (photoDate) {
            photoDate.textContent = date;
        }

        if (deleteForm) {
            deleteForm.action =
                photo.dataset.deleteUrl ||
                (
                    '/delete/' +
                    encodeURIComponent(filename) +
                    '/'
                );
        }

        if (downloadButton) {
            downloadButton.href =
                photo.dataset.downloadUrl ||
                (
                    '/download/' +
                    encodeURIComponent(filename) +
                    '/'
                );
        }

        updatePhotoArrows();
    }

    window.openPhoto = function (photoElement) {
        currentPhotoIndex =
            galleryPhotos.indexOf(photoElement);

        showPhoto(currentPhotoIndex);
    };

    function previousPhoto() {
        if (currentPhotoIndex > 0) {
            currentPhotoIndex--;
            showPhoto(currentPhotoIndex);
        }
    }

    function nextPhoto() {
        if (
            currentPhotoIndex <
            galleryPhotos.length - 1
        ) {
            currentPhotoIndex++;
            showPhoto(currentPhotoIndex);
        }
    }

    function updatePhotoArrows() {
        if (photoPrev) {
            photoPrev.style.visibility =
                currentPhotoIndex === 0
                    ? 'hidden'
                    : 'visible';
        }

        if (photoNext) {
            photoNext.style.visibility =
                currentPhotoIndex ===
                galleryPhotos.length - 1
                    ? 'hidden'
                    : 'visible';
        }
    }

    if (photoPrev) {
        photoPrev.addEventListener(
            'click',
            previousPhoto
        );
    }

    if (photoNext) {
        photoNext.addEventListener(
            'click',
            nextPhoto
        );
    }

    if (deleteForm) {
        deleteForm.addEventListener(
            'submit',
            function (event) {
                const confirmed = confirm(
                    'Вы действительно хотите удалить это фото?'
                );

                if (!confirmed) {
                    event.preventDefault();
                    return;
                }

                if (deleteNext) {
                    const currentUrl =
                        window.location.pathname +
                        window.location.search;

                    deleteNext.value =
                        currentUrl +
                        '#scroll=' +
                        window.scrollY;
                }
            }
        );
    }

    window.closePhoto = function () {
        if (!modal || !modalImage) {
            return;
        }

        modal.classList.remove('active');
        modalImage.src = '';
    };

    if (modal) {
        modal.addEventListener('click', function (event) {
            if (event.target === modal) {
                closePhoto();
            }
        });
    }

    const isPrivateGallery =
    window.location.pathname.startsWith('/private/');

    const photoSelectionStorageKey =
    isPrivateGallery
        ? 'selectedPrivatePhotos'
        : 'selectedPhotos';

    // =========================================================
    // МНОЖЕСТВЕННЫЙ ВЫБОР ФОТО
    // =========================================================

    const selectModeButton = document.getElementById(
        'select-mode-button'
    );

    const bulkActions = document.getElementById(
        'bulk-actions'
    );

    const selectedCount = document.getElementById(
        'selected-count'
    );

    const cancelSelection = document.getElementById(
        'cancel-selection'
    );
    const deleteSelectedButton = document.getElementById(
    'delete-selected'
    );

    if (deleteSelectedButton) {
    deleteSelectedButton.addEventListener(
        'click',
        function () {
            if (selectedPhotos.size === 0) {
                return;
            }

            const confirmed = confirm(
                `Удалить выбранные фото: ${selectedPhotos.size} шт.?`
            );

            if (!confirmed) {
                return;
            }

            const form = document.createElement('form');

            form.method = 'POST';
            form.action = isPrivateGallery
                ? '/private/delete-selected/'
                : '/delete-selected/';

            const csrfToken = document.querySelector(
                '[name=csrfmiddlewaretoken]'
            );

            if (csrfToken) {
                const csrfInput =
                    document.createElement('input');

                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = csrfToken.value;

                form.appendChild(csrfInput);
            }

            selectedPhotos.forEach(function (filename) {
                const input =
                    document.createElement('input');

                input.type = 'hidden';
                input.name = 'photos';
                input.value = filename;

                form.appendChild(input);
            });

            document.body.appendChild(form);
            sessionStorage.removeItem(
                photoSelectionStorageKey
            );
            form.submit();
        }
    );
}

    const downloadSelectedButton = document.getElementById(
        'download-selected'
    );

    if (downloadSelectedButton) {
    downloadSelectedButton.addEventListener(
        'click',
        async function () {
            if (selectedPhotos.size === 0) {
                return;
            }

            const files = [];

            try {
                for (const filename of selectedPhotos) {
                    let photoUrl;

                    if (isPrivateGallery) {
                        photoUrl =
                            '/private/photo/' +
                            encodeURIComponent(filename) +
                            '/';
                    } else {
                        photoUrl =
                            '/media/photos/common/' +
                            encodeURIComponent(filename);
                    }

                    const response = await fetch(photoUrl);

                    if (!response.ok) {
                        continue;
                    }

                    const blob = await response.blob();

                    const file = new File(
                        [blob],
                        filename,
                        {
                            type: blob.type || 'image/jpeg'
                        }
                    );

                    files.push(file);
                }

                if (files.length === 0) {
                    alert('Не удалось получить фотографии');
                    return;
                }

                if (
                    navigator.canShare &&
                    navigator.canShare({ files: files }) &&
                    navigator.share
                ) {
                    await navigator.share({
                        files: files
                    });

                    selectionMode = false;
                    clearSelection();

                    if (selectModeButton) {
                        selectModeButton.classList.remove('hidden');
                    }

                    return;
                }

                downloadFilesNormally(files);
                selectionMode = false;
                clearSelection();

                if (selectModeButton) {
                    selectModeButton.classList.remove('hidden');
                }
                } catch (error) {
                    console.error(error);

                    alert(
                        'Не удалось подготовить фотографии'
                    );
            }
        }
    );
}
    function downloadFilesNormally(files) {
    files.forEach(function (file) {
        const url = URL.createObjectURL(file);

        const link = document.createElement('a');

        link.href = url;
        link.download = file.name;

        document.body.appendChild(link);

        link.click();
        link.remove();

        URL.revokeObjectURL(url);
    });
}


    const savedSelection = JSON.parse(
        sessionStorage.getItem(photoSelectionStorageKey) || '[]'
    );

    const selectedPhotos = new Set(savedSelection);

    function saveSelection() {
        sessionStorage.setItem(
            photoSelectionStorageKey,
            JSON.stringify(Array.from(selectedPhotos))
        );
    }

    let selectionMode = false;

    function updateSelectionUI() {
        if (selectedCount) {
            selectedCount.textContent =
                `Выбрано: ${selectedPhotos.size}`;
        }

        if (bulkActions) {
            bulkActions.classList.toggle(
                'hidden',
                !selectionMode
            );
        }

        document
            .querySelectorAll('.photo[data-filename]')
            .forEach(function (photo) {
                const filename = photo.dataset.filename;

                photo.classList.toggle(
                    'selected',
                    selectedPhotos.has(filename)
                );
            });
    }

    function clearSelection() {
        selectedPhotos.clear();

        sessionStorage.removeItem(
            photoSelectionStorageKey
        );

        document
            .querySelectorAll('.photo.selected')
            .forEach(function (photo) {
                photo.classList.remove('selected');
            });

        updateSelectionUI();
    }

    window.handlePhotoClick = function (photoElement) {
        if (!selectionMode) {
            window.openPhoto(photoElement);
            return;
        }

        const filename =
            photoElement.dataset.filename;

        if (!filename) {
            return;
        }

        if (selectedPhotos.has(filename)) {
            selectedPhotos.delete(filename);
            photoElement.classList.remove('selected');
        } else {
            selectedPhotos.add(filename);
            photoElement.classList.add('selected');
        }

        saveSelection();
        updateSelectionUI();

    };

    if (selectModeButton) {
        selectModeButton.addEventListener(
            'click',
            function () {
                selectionMode = true;

                selectModeButton.classList.add(
                    'hidden'
                );

                updateSelectionUI();
            }
        );
    }

    if (cancelSelection) {
        cancelSelection.addEventListener(
            'click',
            function () {
                selectionMode = false;

                clearSelection();

                if (selectModeButton) {
                    selectModeButton.classList.remove(
                        'hidden'
                    );
                }
            }
        );
    }

    if (selectedPhotos.size > 0) {
        selectionMode = true;

        if (selectModeButton) {
            selectModeButton.classList.add('hidden');
        }
    }

    updateSelectionUI();


    // =========================================================
    // КЛАВИАТУРА
    // =========================================================

    document.addEventListener(
        'keydown',
        function (event) {
            if (
                videoModal &&
                videoModal.classList.contains('active')
            ) {
                if (event.key === 'Escape') {
                    closeVideo();
                }

                return;
            }

            if (
                !modal ||
                !modal.classList.contains('active')
            ) {
                return;
            }

            if (event.key === 'Escape') {
                closePhoto();
            }

            if (event.key === 'ArrowLeft') {
                previousPhoto();
            }

            if (event.key === 'ArrowRight') {
                nextPhoto();
            }
        }
    );
});


// =============================================================
// АДАПТИВНАЯ ПАГИНАЦИЯ
// =============================================================

function isMobileDevice() {
    return (
        window.matchMedia(
            '(pointer: coarse)'
        ).matches ||
        screen.width <= 600
    );
}


function calculatePhotosPerPage() {
    const gallery = document.querySelector('.gallery');

    if (!gallery) {
        return;
    }

    const rootStyles = getComputedStyle(
        document.documentElement
    );

    const minWidth = Number.parseFloat(
        rootStyles.getPropertyValue(
            '--photo-min-width'
        )
    );

    const photoHeight = Number.parseFloat(
        rootStyles.getPropertyValue(
            '--photo-height'
        )
    );

    const gap = Number.parseFloat(
        rootStyles.getPropertyValue(
            '--gallery-gap'
        )
    );

    const galleryWidth = gallery.clientWidth;

    const columns = Math.max(
        1,
        Math.floor(
            (galleryWidth + gap) /
            (minWidth + gap)
        )
    );

    const galleryTop =
        gallery.getBoundingClientRect().top;

    const bottomSpace = 100;

    const availableHeight =
        window.innerHeight -
        galleryTop -
        bottomSpace;

    const rows = Math.max(
        1,
        Math.floor(
            (availableHeight + gap) /
            (photoHeight + gap)
        )
    );

    let perPage;

    if (isMobileDevice()) {
        perPage = 12;
    } else {
        perPage = columns * rows;
    }

    const params = new URLSearchParams(
        window.location.search
    );

    const currentPerPage =
        Number.parseInt(
            params.get('per_page'),
            10
        ) || 0;

    if (currentPerPage === 0) {
        params.set('per_page', perPage);

        window.location.search =
            params.toString();

        return;
    }

    if (
        Math.abs(
            currentPerPage - perPage
        ) >= 2
    ) {
        params.set('per_page', perPage);
        params.set('page', 1);

        window.location.search =
            params.toString();
    }
}


calculatePhotosPerPage();

let resizeTimer;

window.addEventListener(
    'resize',
    function () {
        if (isMobileDevice()) {
            return;
        }

        clearTimeout(resizeTimer);

        resizeTimer = setTimeout(
            function () {
                calculatePhotosPerPage();
            },
            300
        );
    }
);


window.addEventListener(
    'pageshow',
    function () {
        const videoProgress =
            document.getElementById(
                'video-upload-progress'
            );

        if (videoProgress) {
            videoProgress.classList.add(
                'hidden'
            );
        }
    }
);

window.addEventListener('load', function () {
    const hash = window.location.hash;

    if (!hash.startsWith('#scroll=')) {
        return;
    }

    const scrollY = Number(
        hash.replace('#scroll=', '')
    );

    if (!Number.isNaN(scrollY)) {
        window.scrollTo(0, scrollY);
    }

    history.replaceState(
        null,
        '',
        window.location.pathname +
        window.location.search
    );
});