(function () {
    'use strict';

    // ── State ──
    var selectedPlatforms = new Set();
    var imageFile = null;
    var imageDataUrl = null;
    var generationResult = null;
    var currentStep = 0;
    var steps = ['stepSource', 'stepConfigure', 'stepResults'];

    // ── DOM refs ──
    var dropZone = document.getElementById('dropZone');
    var fileInput = document.getElementById('fileInput');
    var previewImg = document.getElementById('previewImg');
    var previewBadges = document.getElementById('previewBadges');
    var previewWarnings = document.getElementById('previewWarnings');
    var previewStrip = document.getElementById('previewStrip');
    var previewRow = document.getElementById('previewRow');
    var shapePreview = document.getElementById('shapePreview');
    var shapeRow = document.getElementById('shapeRow');
    var platformGrid = document.getElementById('platformGrid');
    var toggleAllBtn = document.getElementById('toggleAll');
    var androidOptions = document.getElementById('androidOptions');
    var androidBg = document.getElementById('androidBg');
    var androidBgHex = document.getElementById('androidBgHex');
    var paddingSlider = document.getElementById('paddingSlider');
    var paddingValue = document.getElementById('paddingValue');
    var bgColor = document.getElementById('bgColor');
    var bgColor2 = document.getElementById('bgColor2');
    var bgColorEnabled = document.getElementById('bgColorEnabled');
    var bgGradientToggle = document.getElementById('bgGradientToggle');
    var bgModeLabel = document.getElementById('bgModeLabel');
    var bgGradientMode = false;
    var results = document.getElementById('results');
    var summaryBar = document.getElementById('summaryBar');
    var resultCards = document.getElementById('resultCards');
    var toastContainer = document.getElementById('toastContainer');
    var changeImage = document.getElementById('changeImage');

    var previewModal = document.getElementById('previewModal');
    var modalTitle = document.getElementById('modalTitle');
    var modalPreview = document.getElementById('modalPreview');
    var modalMeta = document.getElementById('modalMeta');
    var modalClose = document.getElementById('modalClose');

    // Bottom bar
    var btnBack = document.getElementById('btnBack');
    var btnNext = document.getElementById('btnNext');
    var bottombarRight = document.getElementById('bottombarRight');

    // Step dots
    var stepDots = document.querySelectorAll('.step-dot');

    var PREVIEW_SIZES = [16, 32, 64, 128, 256, 512];
    var PLATFORM_SHAPES = [
        { id: 'ios', label: 'iOS', cssClass: 'ios' },
        { id: 'android', label: 'Android', cssClass: 'android' },
        { id: 'macos', label: 'macOS', cssClass: 'macos' },
        { id: 'windows', label: 'Windows', cssClass: 'windows' },
        { id: 'web', label: 'Web', cssClass: 'web' },
        { id: 'linux', label: 'Linux', cssClass: 'linux' },
    ];
    var PLATFORM_ICONS = {
        ios: 'smartphone',
        android: 'tablet-smartphone',
        macos: 'monitor',
        windows: 'app-window',
        web: 'globe',
        linux: 'terminal'
    };
    var PLATFORM_NAMES = {
        ios: 'iOS',
        android: 'Android',
        macos: 'macOS',
        windows: 'Windows',
        web: 'Web / PWA',
        linux: 'Linux'
    };

    // ── Step navigation ──
    function goToStep(index) {
        if (index < 0 || index >= steps.length) return;
        if (index === currentStep) return;

        var stepEls = steps.map(function (id) { return document.getElementById(id); });

        stepEls.forEach(function (el, i) {
            el.classList.remove('step--active', 'step--left', 'step--right');
            if (i < index) {
                el.classList.add('step--left');
            } else if (i > index) {
                el.classList.add('step--right');
            } else {
                el.classList.add('step--active');
            }
        });

        currentStep = index;
        updateStepDots();
        updateBottomBar();
    }

    function updateStepDots() {
        stepDots.forEach(function (dot, i) {
            dot.classList.remove('step-dot--active', 'step-dot--completed');
            dot.removeAttribute('aria-current');
            if (i === currentStep) {
                dot.classList.add('step-dot--active');
                dot.setAttribute('aria-current', 'step');
            } else if (i < currentStep) {
                dot.classList.add('step-dot--completed');
            }
        });
    }

    function updateBottomBar() {
        // Clear right side
        bottombarRight.innerHTML = '';

        if (currentStep === 0) {
            // Step 1: Source
            btnBack.disabled = true;
            btnBack.style.visibility = 'hidden';

            var next = document.createElement('button');
            next.className = 'bottombar__btn bottombar__btn--primary';
            next.id = 'btnNext';
            next.disabled = !imageFile;
            next.innerHTML = 'Next <i data-lucide="arrow-right" size="14"></i>';
            next.addEventListener('click', function () { goToStep(1); });
            bottombarRight.appendChild(next);
            btnNext = next;

        } else if (currentStep === 1) {
            // Step 2: Configure
            btnBack.disabled = false;
            btnBack.style.visibility = 'visible';

            var generate = document.createElement('button');
            generate.className = 'bottombar__btn bottombar__btn--primary';
            generate.id = 'btnGenerate';
            generate.disabled = selectedPlatforms.size === 0;
            generate.innerHTML = '<i data-lucide="zap" size="14"></i> Generate';
            generate.addEventListener('click', doGenerate);
            bottombarRight.appendChild(generate);

        } else if (currentStep === 2) {
            // Step 3: Results
            btnBack.style.visibility = 'visible';
            btnBack.disabled = false;

            // Replace back text with "Start Over"
            btnBack.innerHTML = '<i data-lucide="rotate-ccw" size="14"></i> Start Over';

            var dlBtn = document.createElement('a');
            dlBtn.href = '/api/download';
            dlBtn.download = 'glyphkit-output.zip';
            dlBtn.className = 'bottombar__btn bottombar__btn--primary';
            dlBtn.innerHTML = '<i data-lucide="download" size="14"></i> Download ZIP';
            bottombarRight.appendChild(dlBtn);

            var openBtn = document.createElement('button');
            openBtn.className = 'bottombar__btn';
            openBtn.innerHTML = '<i data-lucide="folder-open" size="14"></i> Open Folder';
            openBtn.addEventListener('click', doOpenFolder);
            bottombarRight.appendChild(openBtn);

            var copyBtn = document.createElement('button');
            copyBtn.className = 'bottombar__btn';
            copyBtn.innerHTML = '<i data-lucide="clipboard-copy" size="14"></i> Copy Path';
            copyBtn.addEventListener('click', doCopyPath);
            bottombarRight.appendChild(copyBtn);
        }

        lucide.createIcons();
    }

    // Back button
    btnBack.addEventListener('click', function () {
        if (currentStep === 2) {
            // Start over — go to step 0
            goToStep(0);
            // Reset back button text
            btnBack.innerHTML = '<i data-lucide="arrow-left" size="14"></i> Back';
        } else {
            goToStep(currentStep - 1);
        }
    });

    // Step dot clicks
    stepDots.forEach(function (dot) {
        dot.addEventListener('click', function () {
            var target = parseInt(dot.dataset.step, 10);
            // Only allow going to completed steps or current+1 if valid
            if (target <= currentStep) {
                goToStep(target);
            } else if (target === 1 && imageFile) {
                goToStep(1);
            }
            // Don't allow jumping to results
        });
    });

    // ── Toast ──
    function showToast(message, type) {
        type = type || 'error';
        var toast = document.createElement('div');
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

        modalPreview.innerHTML = '';
        var img = document.createElement('img');
        img.src = file.preview_url;
        img.alt = file.name;
        if (file.size > 0 && file.size <= 64) {
            img.classList.add('pixelated');
            img.style.width = Math.max(file.size * 4, 128) + 'px';
            img.style.height = Math.max(file.size * 4, 128) + 'px';
        }
        modalPreview.appendChild(img);

        modalMeta.innerHTML = '';
        if (file.size > 0) {
            modalMeta.innerHTML += '<div class="modal__meta-item">' +
                '<span class="modal__meta-key">Size</span>' +
                '<span class="modal__meta-value">' + file.size + ' \u00D7 ' + file.size + '</span></div>';
        }
        modalMeta.innerHTML += '<div class="modal__meta-item">' +
            '<span class="modal__meta-key">File</span>' +
            '<span class="modal__meta-value">' + file.name + '</span></div>';

        previewModal.style.display = 'flex';
        requestAnimationFrame(function () {
            previewModal.classList.add('visible');
        });
    }

    function closePreviewModal() {
        previewModal.classList.remove('visible');
        previewModal.addEventListener('transitionend', function handler() {
            previewModal.removeEventListener('transitionend', handler);
            previewModal.style.display = 'none';
            modalPreview.innerHTML = '';
            modalMeta.innerHTML = '';
        });
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

    // ── Update bottom bar state ──
    function updateNextBtn() {
        if (currentStep === 0 && btnNext) {
            btnNext.disabled = !imageFile;
        }
        if (currentStep === 1) {
            var genBtn = document.getElementById('btnGenerate');
            if (genBtn) genBtn.disabled = selectedPlatforms.size === 0;
        }
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

            updatePreviews();
            updateNextBtn();

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

        var pad = pct > 0 ? Math.round(img.width * pct / 100) : 0;
        var newSize = img.width + pad * 2;

        var canvas = document.createElement('canvas');
        canvas.width = newSize;
        canvas.height = newSize;
        var ctx = canvas.getContext('2d');

        if (hasBg) {
            if (bgGradientMode) {
                var grad = ctx.createLinearGradient(0, 0, newSize, newSize);
                grad.addColorStop(0, bgColor.value);
                grad.addColorStop(1, bgColor2.value);
                ctx.fillStyle = grad;
            } else {
                ctx.fillStyle = bgColor.value;
            }
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
        updateNextBtn();
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
        updateNextBtn();
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
        var on = bgColorEnabled.checked;
        bgColor.disabled = !on;
        bgGradientToggle.style.display = on ? '' : 'none';
        if (!on) {
            bgGradientMode = false;
            bgColor2.style.display = 'none';
            bgGradientToggle.textContent = 'Gradient';
            bgModeLabel.textContent = 'Solid';
        }
        updatePreviews();
    });

    bgGradientToggle.addEventListener('click', function () {
        bgGradientMode = !bgGradientMode;
        bgColor2.style.display = bgGradientMode ? '' : 'none';
        bgColor2.disabled = !bgGradientMode;
        bgGradientToggle.textContent = bgGradientMode ? 'Solid' : 'Gradient';
        bgModeLabel.textContent = bgGradientMode ? 'Gradient' : 'Solid';
        updatePreviews();
    });

    bgColor.addEventListener('input', function () {
        updatePreviews();
    });

    bgColor2.addEventListener('input', function () {
        updatePreviews();
    });

    // ── Generate ──
    async function doGenerate() {
        var genBtn = document.getElementById('btnGenerate');
        if (!genBtn || genBtn.disabled) return;

        genBtn.disabled = true;
        genBtn.innerHTML = '<i data-lucide="loader" size="14"></i> Generating\u2026';
        genBtn.classList.add('loading');
        lucide.createIcons();
        results.classList.remove('visible');

        var formData = new FormData();
        formData.append('image', imageFile);
        formData.append('platforms', JSON.stringify(Array.from(selectedPlatforms)));
        formData.append('android_bg', androidBg.value);
        formData.append('padding', paddingSlider.value);
        if (bgColorEnabled.checked) {
            if (bgGradientMode) {
                formData.append('bg_color', bgColor.value + ',' + bgColor2.value);
            } else {
                formData.append('bg_color', bgColor.value);
            }
        } else {
            formData.append('bg_color', '');
        }

        try {
            var resp = await fetch('/api/generate', { method: 'POST', body: formData });
            var data = await resp.json();

            if (!resp.ok) {
                showToast(data.detail || 'Generation failed. Check your image and try again.');
                genBtn.disabled = false;
                genBtn.innerHTML = '<i data-lucide="zap" size="14"></i> Generate';
                genBtn.classList.remove('loading');
                lucide.createIcons();
                return;
            }

            generationResult = data;

            // Success — go to results step
            genBtn.classList.remove('loading');
            genBtn.classList.add('success');
            genBtn.innerHTML = '\u2713 Done';

            renderResults(data);

            setTimeout(function () {
                goToStep(2);
            }, 400);

        } catch (err) {
            showToast('Can\u2019t reach the server. Is glyphkit still running?');
            genBtn.classList.remove('loading');
            genBtn.innerHTML = '<i data-lucide="zap" size="14"></i> Generate';
            genBtn.disabled = false;
            lucide.createIcons();
        }
    }

    // ── Open folder ──
    async function doOpenFolder() {
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
    }

    // ── Copy path ──
    async function doCopyPath() {
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
    }

    // ── Render results ──
    function renderResults(data) {
        var platforms = data.platforms;
        var totalFiles = 0;
        Object.values(platforms).forEach(function (p) { totalFiles += p.file_count; });

        // Summary
        summaryBar.innerHTML = '<div class="summary-bar__text"><strong>' + totalFiles + ' files</strong> generated across ' + Object.keys(platforms).length + ' platform' + (Object.keys(platforms).length > 1 ? 's' : '') + '</div>';

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
    }

    // ── Keyboard shortcuts ──
    document.addEventListener('keydown', function (e) {
        // Don't intercept if modal is open or inside an input
        if (previewModal.classList.contains('visible')) return;
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        if (e.key === 'ArrowRight' && currentStep === 0 && imageFile) {
            goToStep(1);
        } else if (e.key === 'ArrowLeft' && currentStep > 0) {
            if (currentStep === 2) {
                goToStep(0);
                btnBack.innerHTML = '<i data-lucide="arrow-left" size="14"></i> Back';
            } else {
                goToStep(currentStep - 1);
            }
        }
    });

    // Initialize
    updateBottomBar();
    lucide.createIcons();

})();
