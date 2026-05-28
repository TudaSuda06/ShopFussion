(function () {
    var theme = localStorage.getItem('theme') || 'light';
    if (theme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
})();

document.addEventListener('DOMContentLoaded', function () {
    var themeToggle = document.getElementById('theme-toggle');
    var themeIcon = document.getElementById('theme-icon');
    if (themeToggle && themeIcon) {
        var cur = document.documentElement.getAttribute('data-theme');
        themeIcon.className = cur === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        themeToggle.addEventListener('click', function () {
            var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            var next = isDark ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('theme', next);
            themeIcon.className = next === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        });
    }
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (el) {
        return new bootstrap.Tooltip(el);
    });

    var alertList = document.querySelectorAll('.alert');
    alertList.forEach(function (alert) {
        setTimeout(function () {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    var quantityForms = document.querySelectorAll('.cart-item form');
    quantityForms.forEach(function (form) {
        var buttons = form.querySelectorAll('button[type="submit"]');
        buttons.forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                var val = parseInt(btn.value);
                if (val <= 0) {
                    e.preventDefault();
                }
            });
        });
    });

    var extraChars = document.getElementById('extra-chars');
    if (extraChars) {
        var charCount = 0;
        var existingRows = extraChars.querySelectorAll('.char-row');
        existingRows.forEach(function (row) {
            var nameInput = row.querySelector('input[name^="char_name_"]');
            if (nameInput) {
                var idx = nameInput.name.replace('char_name_', '');
                if (idx && !isNaN(idx)) {
                    charCount = Math.max(charCount, parseInt(idx) + 1);
                }
            }
            var removeBtn = row.querySelector('.remove-char-btn');
            if (removeBtn) {
                removeBtn.addEventListener('click', function () {
                    if (extraChars.querySelectorAll('.char-row').length > 1) {
                        row.remove();
                    }
                });
            }
        });

        extraChars.addEventListener('click', function (e) {
            if (e.target.closest('.add-char-btn')) {
                var newRow = document.createElement('div');
                newRow.className = 'row g-2 mb-2 char-row';
                newRow.innerHTML = [
                    '<div class="col-5">',
                    '<input type="text" name="char_name_' + charCount + '" class="form-control" placeholder="Название">',
                    '</div>',
                    '<div class="col-5">',
                    '<input type="text" name="char_value_' + charCount + '" class="form-control" placeholder="Значение">',
                    '</div>',
                    '<div class="col-2">',
                    '<button type="button" class="btn btn-outline-danger remove-char-btn w-100"><i class="fas fa-times"></i></button>',
                    '</div>',
                    '</div>'
                ].join('');
                var addRow = extraChars.querySelector('.char-row:last-child');
                addRow.parentNode.insertBefore(newRow, addRow.nextSibling);
                var removeBtn = newRow.querySelector('.remove-char-btn');
                removeBtn.addEventListener('click', function () {
                    if (extraChars.querySelectorAll('.char-row').length > 1) {
                        newRow.remove();
                    }
                });
                charCount++;
            }
        });
    }

    var searchInput = document.getElementById('search-input');
    var suggestionsBox = document.getElementById('search-suggestions');
    if (searchInput && suggestionsBox) {
        var timeout = null;
        searchInput.addEventListener('input', function () {
            clearTimeout(timeout);
            var q = searchInput.value.trim();
            if (q.length < 2) {
                suggestionsBox.style.display = 'none';
                return;
            }
            timeout = setTimeout(function () {
                fetch('/search/suggestions?q=' + encodeURIComponent(q))
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        if (data.length === 0) {
                            suggestionsBox.style.display = 'none';
                            return;
                        }
                        suggestionsBox.innerHTML = data.map(function (p) {
                            return '<a href="/product/' + p.id + '" class="dropdown-item d-flex align-items-center gap-2">' +
                                '<img src="' + p.image + '" style="width: 32px; height: 32px; object-fit: cover; border-radius: 4px;">' +
                                '<div class="flex-grow-1"><small class="fw-bold d-block">' + p.name.slice(0, 40) + '</small><small class="text-warning">' + p.price.toFixed(2) + ' \u20BD</small></div>' +
                                '</a>';
                        }).join('');
                        suggestionsBox.style.display = 'block';
                    });
            }, 300);
        });
        document.addEventListener('click', function (e) {
            if (!searchInput.contains(e.target) && !suggestionsBox.contains(e.target)) {
                suggestionsBox.style.display = 'none';
            }
        });
    }
});
