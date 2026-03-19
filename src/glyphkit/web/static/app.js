(function () {
    'use strict';

    // ── State ──
    let selectedPlatforms = new Set();
    let imageFile = null;
    let imageDataUrl = null;
    let generationResult = null;

    // ── DOM refs ──
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const previewImg = document.getElementById('previewImg');
    const previewBadges = document.getElementById('previewBadges');
    const previewWarnings = document.getElementById('previewWarnings');
    const previewStrip = document.getElementById('previewStrip');
    const previewRow = document.getElementById('previewRow');
    const shapePreview = document.getElementById('shapePreview');
    const shapeRow = document.getElementById('shapeRow');
    const platformGrid = document.getElementById('platformGrid');
    const toggleAllBtn = document.getElementById('toggleAll');
    const androidOptions = document.getElementById('androidOptions');
    const androidBg = document.getElementById('androidBg');
    const androidBgHex = document.getElementById('androidBgHex');
    const paddingSlider = document.getElementById('paddingSlider');
    const paddingValue = document.getElementById('paddingValue');
    const bgColor = document.getElementById('bgColor');
    const bgColorEnabled = document.getElementById('bgColorEnabled');
    const generateBtn = document.getElementById('generateBtn');
    const results = document.getElementById('results');
    const summaryBar = document.getElementById('summaryBar');
    const resultCards = document.getElementById('resultCards');
    const toastContainer = document.getElementById('toastContainer');
    const changeImage = document.getElementById('changeImage');

    const previewModal = document.getElementById('previewModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalPreview = document.getElementById('modalPreview');
    const modalMeta = document.getElementById('modalMeta');
    const modalClose = document.getElementById('modalClose');

    const PREVIEW_SIZES = [16, 32, 64, 128, 256, 512];
    const PLATFORM_SHAPES = [
        { id: 'ios', label: 'iOS', cssClass: 'ios' },
        { id: 'android', label: 'Android', cssClass: 'android' },
        { id: 'macos', label: 'macOS', cssClass: 'macos' },
        { id: 'windows', label: 'Windows', cssClass: 'windows' },
        { id: 'web', label: 'Web', cssClass: 'web' },
        { id: 'linux', label: 'Linux', cssClass: 'linux' },
    ];
    const PLATFORM_ICONS = {
        ios: 'smartphone',
        android: 'tablet-smartphone',
        macos: 'monitor',
        windows: 'app-window',
        web: 'globe',
        linux: 'terminal'
    };
    const PLATFORM_NAMES = {
        ios: 'iOS',
        android: 'Android',
        macos: 'macOS',
        windows: 'Windows',
        web: 'Web / PWA',
        linux: 'Linux'
    };

    // ── Toast ──
    function showToast(message, type) {
        type = type || 'error';
        const toast = document.createElement('div');
        toast.className = 'toast' + (type === 'success' ? ' toast--success' : '');
        toast.textContent = message;
        toastContainer.appendChild(toast);
        setTimeout(function () {
            toast.classList.add('dismissing');
            toast.addEventListener('animationend', function () { toast.remove(); });
        }, 5000);
    }

    // ── Preview modal ──
    function openPreviewModal(file, platformName) {
        modalTitle.textContent = file.name;

        // Image preview
        modalPreview.innerHTML = '';
        var img = document.createElement('img');
        img.src = file.preview_url;
        img.alt = file.name;
        // Use pixelated rendering for icons <= 64px so they stay crisp
        if (file.size > 0 && file.size <= 64) {
            img.classList.add('pixelated');
            img.style.width = Math.max(file.size * 4, 128) + 'px';
            img.style.height = Math.max(file.size * 4, 128) + 'px';
        }
        modalPreview.appendChild(img);

        // Metadata — just dimensions and filename
        modalMeta.innerHTML = '';
        if (file.size > 0) {
            modalMeta.innerHTML += '<div class="modal__meta-item">' +
                '<span class="modal__meta-key">Size</span>' +
                '<span class="modal__meta-value">' + file.size + ' \u00D7 ' + file.size + '</span></div>';
        }
        modalMeta.innerHTML += '<div class="modal__meta-item">' +
            '<span class="modal__meta-key">File</span>' +
            '<span class="modal__meta-value">' + file.name + '</span></div>';

        // Show
        previewModal.style.display = 'flex';
        requestAnimationFrame(function () {
            previewModal.classList.add('visible');
        });
        document.body.style.overflow = 'hidden';
    }

    function closePreviewModal() {
        previewModal.classList.remove('visible');
        previewModal.addEventListener('transitionend', function handler() {
            previewModal.removeEventListener('transitionend', handler);
            previewModal.style.display = 'none';
            modalPreview.innerHTML = '';
            modalMeta.innerHTML = '';
        });
        document.body.style.overflow = '';
    }

    previewModal.style.display = 'none';

    modalClose.addEventListener('click', closePreviewModal);
    previewModal.addEventListener('click', function (e) {
        if (e.target === previewModal) closePreviewModal();
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && previewModal.classList.contains('visible')) {
            closePreviewModal();
        }
    });

    // ── Update generate button state ──
    function updateGenerateBtn() {
        generateBtn.disabled = !(imageFile && selectedPlatforms.size > 0);
    }

    // ── Drop zone events ──
    dropZone.addEventListener('click', function (e) {
        if (e.target === changeImage || e.target.closest('.change-image')) return;
        fileInput.click();
    });

    dropZone.addEventListener('keydown', function (e) {
        if (e.key === ' ' || e.key === 'Enter') {
            e.preventDefault();
            fileInput.click();
        }
    });

    changeImage.addEventListener('click', function (e) {
        e.stopPropagation();
        fileInput.click();
    });

    dropZone.addEventListener('dragover', function (e) {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', function (e) {
        e.preventDefault();
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', function (e) {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        var files = e.dataTransfer.files;
        if (files.length > 0) handleFile(files[0]);
    });

    fileInput.addEventListener('change', function () {
        if (fileInput.files.length > 0) handleFile(fileInput.files[0]);
    });

    // ── Handle file selection ──
    function handleFile(file) {
        if (!file.type.match(/^image\/(png|jpeg|webp|svg\+xml)$/)) {
            showToast('Unsupported format. Use PNG, JPEG, WebP, or SVG.');
            return;
        }

        imageFile = file;

        var reader = new FileReader();
        reader.onload = function (e) {
            imageDataUrl = e.target.result;
            previewImg.src = imageDataUrl;
            validateImage(file);
        };
        reader.readAsDataURL(file);
    }

    // ── Validate via API ──
    async function validateImage(file) {
        var formData = new FormData();
        formData.append('image', file);

        try {
            var resp = await fetch('/api/validate', { method: 'POST', body: formData });
            var data = await resp.json();

            if (!resp.ok) {
                showToast(data.detail || 'Could not validate this image. Check that it\u2019s a square image.');
                imageFile = null;
                imageDataUrl = null;
                return;
            }

            // Show preview
            dropZone.classList.add('drop-zone--has-image');
            previewBadges.innerHTML = '';
            previewWarnings.innerHTML = '';

            var dimBadge = document.createElement('span');
            dimBadge.className = 'badge';
            dimBadge.textContent = data.width + ' \u00D7 ' + data.height;
            previewBadges.appendChild(dimBadge);

            if (data.has_transparency) {
                var tBadge = document.createElement('span');
                tBadge.className = 'badge badge--warn';
                tBadge.textContent = 'Transparent \u2014 iOS will add a background';
                previewBadges.appendChild(tBadge);
            }

            if (data.warnings && data.warnings.length > 0) {
                data.warnings.forEach(function (w) {
                    var el = document.createElement('div');
                    el.className = 'warning-text';
                    el.textContent = w;
                    previewWarnings.appendChild(el);
                });
            }

            // Populate previews (applies current padding)
            updatePreviews();
            updateGenerateBtn();

        } catch (err) {
            showToast('Can\u2019t reach the server. Is glyphkit still running?');
        }
    }

    // ── Padded preview generation ──
    var paddedDataUrl = null;

    function getProcessedDataUrl() {
        if (!imageDataUrl) return imageDataUrl;

        var pct = parseInt(paddingSlider.value, 10);
        var hasBg = bgColorEnabled.checked;
        if (pct <= 0 && !hasBg) return imageDataUrl;

        var img = new window.Image();
        img.src = imageDataUrl;

        // Calculate dimensions with padding
        var pad = pct > 0 ? Math.round(img.width * pct / 100) : 0;
        var newSize = img.width + pad * 2;

        var canvas = document.createElement('canvas');
        canvas.width = newSize;
        canvas.height = newSize;
        var ctx = canvas.getContext('2d');

        // Fill background if enabled
        if (hasBg) {
            ctx.fillStyle = bgColor.value;
            ctx.fillRect(0, 0, newSize, newSize);
        }

        ctx.drawImage(img, pad, pad, img.width, img.height);
        return canvas.toDataURL('image/png');
    }

    function updatePreviews() {
        if (!imageDataUrl) return;
        paddedDataUrl = getProcessedDataUrl();
        populatePreviewStrip();
        populateShapePreview();
    }

    // ── Live preview strip ──
    function populatePreviewStrip() {
        var src = paddedDataUrl || imageDataUrl;
        if (!src) return;
        previewRow.innerHTML = '';
        PREVIEW_SIZES.forEach(function (size) {
            var item = document.createElement('div');
            item.className = 'preview-strip__item';

            var wrap = document.createElement('div');
            wrap.className = 'preview-strip__img-wrap';
            var displaySize = Math.min(size, 128);
            wrap.style.width = (displaySize + 8) + 'px';
            wrap.style.height = (displaySize + 8) + 'px';

            var img = document.createElement('img');
            img.src = src;
            img.width = displaySize;
            img.height = displaySize;
            wrap.appendChild(img);

            var label = document.createElement('span');
            label.className = 'preview-strip__size';
            label.textContent = size + 'px';

            item.appendChild(wrap);
            item.appendChild(label);
            previewRow.appendChild(item);
        });
        previewStrip.classList.add('visible');
    }

    // ── Shape preview ──
    function populateShapePreview() {
        var src = paddedDataUrl || imageDataUrl;
        if (!src) return;
        shapeRow.innerHTML = '';
        PLATFORM_SHAPES.forEach(function (shape) {
            var item = document.createElement('div');
            item.className = 'shape-preview__item';

            var mask = document.createElement('div');
            mask.className = 'shape-preview__mask shape-preview__mask--' + shape.cssClass;

            var img = document.createElement('img');
            img.src = src;
            img.alt = shape.label + ' shape';
            mask.appendChild(img);

            var label = document.createElement('span');
            label.className = 'shape-preview__label';
            label.textContent = shape.label;

            item.appendChild(mask);
            item.appendChild(label);
            shapeRow.appendChild(item);
        });
        shapePreview.classList.add('visible');
    }

    // ── Platform selector ──
    var cards = platformGrid.querySelectorAll('.platform-card');

    function togglePlatformCard(card) {
        var p = card.dataset.platform;
        if (selectedPlatforms.has(p)) {
            selectedPlatforms.delete(p);
            card.classList.remove('selected');
            card.setAttribute('aria-checked', 'false');
        } else {
            selectedPlatforms.add(p);
            card.classList.add('selected');
            card.setAttribute('aria-checked', 'true');
        }
        updateAndroidOptions();
        updateGenerateBtn();
        updateToggleLabel();
    }

    cards.forEach(function (card) {
        card.addEventListener('click', function () { togglePlatformCard(card); });
        card.addEventListener('keydown', function (e) {
            if (e.key === ' ' || e.key === 'Enter') {
                e.preventDefault();
                togglePlatformCard(card);
            }
        });
    });

    toggleAllBtn.addEventListener('click', function () {
        if (selectedPlatforms.size === cards.length) {
            selectedPlatforms.clear();
            cards.forEach(function (c) { c.classList.remove('selected'); c.setAttribute('aria-checked', 'false'); });
        } else {
            cards.forEach(function (c) {
                selectedPlatforms.add(c.dataset.platform);
                c.classList.add('selected');
                c.setAttribute('aria-checked', 'true');
            });
        }
        updateAndroidOptions();
        updateGenerateBtn();
        updateToggleLabel();
    });

    function updateToggleLabel() {
        toggleAllBtn.textContent = selectedPlatforms.size === cards.length ? 'Deselect All' : 'Select All';
    }

    function updateAndroidOptions() {
        if (selectedPlatforms.has('android')) {
            androidOptions.classList.add('visible');
        } else {
            androidOptions.classList.remove('visible');
        }
    }

    androidBg.addEventListener('input', function () {
        androidBgHex.textContent = androidBg.value.toUpperCase();
    });

    paddingSlider.addEventListener('input', function () {
        paddingValue.textContent = paddingSlider.value + '%';
        updatePreviews();
    });

    bgColorEnabled.addEventListener('change', function () {
        bgColor.disabled = !bgColorEnabled.checked;
        updatePreviews();
    });

    bgColor.addEventListener('input', function () {
        updatePreviews();
    });

    // ── Generate ──
    generateBtn.addEventListener('click', async function () {
        if (generateBtn.disabled) return;

        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating\u2026';
        generateBtn.classList.add('loading');
        results.classList.remove('visible');

        var formData = new FormData();
        formData.append('image', imageFile);
        formData.append('platforms', JSON.stringify(Array.from(selectedPlatforms)));
        formData.append('android_bg', androidBg.value);
        formData.append('padding', paddingSlider.value);
        formData.append('bg_color', bgColorEnabled.checked ? bgColor.value : '');

        try {
            var resp = await fetch('/api/generate', { method: 'POST', body: formData });
            var data = await resp.json();

            if (!resp.ok) {
                showToast(data.detail || 'Generation failed. Check your image and try again.');
                generateBtn.disabled = false;
                generateBtn.textContent = 'Generate Icons';
                generateBtn.classList.remove('loading');
                return;
            }

            generationResult = data;

            // Brief success flash
            generateBtn.classList.remove('loading');
            generateBtn.classList.add('success');
            generateBtn.textContent = '\u2713 Done';
            setTimeout(function () {
                generateBtn.classList.remove('success');
                generateBtn.textContent = 'Generate Icons';
                updateGenerateBtn();
            }, 1200);

            renderResults(data);

        } catch (err) {
            showToast('Can\u2019t reach the server. Is glyphkit still running?');
            generateBtn.classList.remove('loading');
            generateBtn.textContent = 'Generate Icons';
            updateGenerateBtn();
        }
    });

    // ── Render results ──
    function renderResults(data) {
        var platforms = data.platforms;
        var totalFiles = 0;
        Object.values(platforms).forEach(function (p) { totalFiles += p.file_count; });

        // Summary
        summaryBar.innerHTML = '<div class="summary-bar__text"><strong>' + totalFiles + ' files</strong> generated across ' + Object.keys(platforms).length + ' platform' + (Object.keys(platforms).length > 1 ? 's' : '') + '</div>' +
            '<div class="summary-bar__actions">' +
            '<a href="/api/download" download="glyphkit-output.zip" class="btn-outline"><i data-lucide="download" size="14"></i> Download ZIP</a>' +
            '<button class="btn-outline" id="openFolderBtn"><i data-lucide="folder-open" size="14"></i> Open Folder</button>' +
            '<button class="btn-outline" id="copyPathBtn"><i data-lucide="clipboard-copy" size="14"></i> Copy Path</button>' +
            '</div>';

        document.getElementById('openFolderBtn').addEventListener('click', async function () {
            try {
                var resp = await fetch('/api/open-folder', { method: 'POST' });
                if (resp.ok) {
                    showToast('Icons saved and folder opened', 'success');
                } else {
                    var errData = await resp.json();
                    showToast(errData.detail || 'Could not open the output folder');
                }
            } catch (err) {
                showToast('Can\u2019t reach the server. Is glyphkit still running?');
            }
        });

        document.getElementById('copyPathBtn').addEventListener('click', async function () {
            try {
                var resp = await fetch('/api/copy-path', { method: 'POST' });
                var data = await resp.json();
                if (resp.ok && data.path) {
                    await navigator.clipboard.writeText(data.path);
                    showToast('Path copied to clipboard', 'success');
                } else {
                    showToast(data.detail || 'Could not save output');
                }
            } catch (err) {
                showToast('Could not copy to clipboard');
            }
        });

        // Platform cards
        resultCards.innerHTML = '';
        var delay = 0;
        for (var platformName in platforms) {
            var pData = platforms[platformName];
            var card = document.createElement('div');
            card.className = 'result-card glass';
            card.style.animationDelay = delay + 'ms';

            var iconName = PLATFORM_ICONS[platformName] || 'box';
            var displayName = PLATFORM_NAMES[platformName] || platformName;

            card.innerHTML = '<div class="result-card__header">' +
                '<div class="result-card__left">' +
                '<i data-lucide="' + iconName + '" size="16"></i>' +
                '<span class="result-card__platform">' + displayName + '</span>' +
                '<span class="result-card__count">' + pData.file_count + ' file' + (pData.file_count > 1 ? 's' : '') + '</span>' +
                '</div>' +
                '<i data-lucide="chevron-down" size="14" class="result-card__chevron"></i>' +
                '</div>' +
                '<div class="result-card__body"><div class="icon-grid"></div></div>';

            var grid = card.querySelector('.icon-grid');
            // Sort: images first (by size descending), then non-images
            var sortedFiles = pData.files.slice().sort(function (a, b) {
                var aImg = /\.(png|ico)$/i.test(a.name) ? 1 : 0;
                var bImg = /\.(png|ico)$/i.test(b.name) ? 1 : 0;
                if (aImg !== bImg) return bImg - aImg;
                return b.size - a.size;
            });
            sortedFiles.forEach(function (file, idx) {
                var item = document.createElement('div');
                item.className = 'icon-grid__item';
                item.style.animationDelay = (idx * 30) + 'ms';

                var thumb = document.createElement('div');
                thumb.className = 'icon-grid__thumb';

                var isImage = /\.(png|ico)$/i.test(file.name);
                if (isImage) {
                    item.classList.add('icon-grid__item--clickable');
                    var img = document.createElement('img');
                    img.src = file.preview_url;
                    img.alt = file.name;
                    img.loading = 'lazy';
                    thumb.appendChild(img);
                    (function (f, pName) {
                        item.addEventListener('click', function () {
                            openPreviewModal(f, pName);
                        });
                    })(file, platformName);
                } else {
                    thumb.classList.add('icon-grid__thumb--file');
                    thumb.innerHTML = '<i data-lucide="file-text" size="28"></i>';
                }
                item.appendChild(thumb);

                var label = document.createElement('div');
                label.className = 'icon-grid__label';
                label.textContent = file.name;
                if (file.size > 0) {
                    label.innerHTML = file.name + ' <span class="size-tag">' + file.size + '\u00D7' + file.size + '</span>';
                }
                label.title = file.name + (file.size > 0 ? ' (' + file.size + '\u00D7' + file.size + ')' : '');
                item.appendChild(label);
                grid.appendChild(item);
            });

            // Toggle expand
            (function (c) {
                c.querySelector('.result-card__header').addEventListener('click', function () {
                    c.classList.toggle('expanded');
                });
            })(card);

            resultCards.appendChild(card);
            delay += 50;
        }

        results.classList.add('visible');
        lucide.createIcons();

        // Scroll into view
        results.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Initialize Lucide icons on page load
    lucide.createIcons();

})();
