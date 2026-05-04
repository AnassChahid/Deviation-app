(function () {
    function getSelectedText(select) {
        const selected = select.options[select.selectedIndex];
        return selected && selected.text ? selected.text : 'Select option';
    }

    function closeAll(except) {
        document.querySelectorAll('.app-searchable-select.is-open').forEach(function (widget) {
            if (widget !== except) {
                widget.classList.remove('is-open');
            }
        });
    }

    function renderOptions(select, optionsBox, triggerText, query) {
        const normalizedQuery = query.trim().toLowerCase();
        let matches = 0;
        optionsBox.innerHTML = '';

        Array.from(select.options).forEach(function (option) {
            const label = option.text || '';
            if (normalizedQuery && !label.toLowerCase().includes(normalizedQuery)) {
                return;
            }

            matches += 1;
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'app-searchable-option';
            button.textContent = label;
            button.dataset.value = option.value;
            if (option.selected) {
                button.classList.add('is-selected');
            }
            button.addEventListener('click', function () {
                select.value = option.value;
                select.dispatchEvent(new Event('change', { bubbles: true }));
                triggerText.textContent = getSelectedText(select);
                closeAll();
            });
            optionsBox.appendChild(button);
        });

        if (!matches) {
            const empty = document.createElement('div');
            empty.className = 'app-searchable-empty';
            empty.textContent = 'No matching values';
            optionsBox.appendChild(empty);
        }
    }

    function enhance(select) {
        if (select.dataset.searchableReady === 'true') {
            return;
        }
        select.dataset.searchableReady = 'true';
        select.classList.add('app-searchable-native');

        const widget = document.createElement('div');
        widget.className = 'app-searchable-select';

        const trigger = document.createElement('button');
        trigger.type = 'button';
        trigger.className = 'app-searchable-trigger';
        trigger.setAttribute('aria-haspopup', 'listbox');

        const triggerText = document.createElement('span');
        triggerText.textContent = getSelectedText(select);
        const icon = document.createElement('i');
        icon.className = 'feather icon-chevron-down';
        trigger.appendChild(triggerText);
        trigger.appendChild(icon);

        const menu = document.createElement('div');
        menu.className = 'app-searchable-menu';

        const search = document.createElement('input');
        search.type = 'search';
        search.className = 'form-control app-searchable-input';
        search.placeholder = select.dataset.searchPlaceholder || 'Search';
        search.autocomplete = 'off';

        const optionsBox = document.createElement('div');
        optionsBox.className = 'app-searchable-options';
        optionsBox.setAttribute('role', 'listbox');

        menu.appendChild(search);
        menu.appendChild(optionsBox);
        widget.appendChild(trigger);
        widget.appendChild(menu);
        select.insertAdjacentElement('afterend', widget);

        trigger.addEventListener('click', function () {
            const isOpen = widget.classList.contains('is-open');
            closeAll(widget);
            widget.classList.toggle('is-open', !isOpen);
            renderOptions(select, optionsBox, triggerText, search.value);
            if (!isOpen) {
                search.focus();
                search.select();
            }
        });

        search.addEventListener('input', function () {
            renderOptions(select, optionsBox, triggerText, search.value);
        });

        search.addEventListener('keydown', function (event) {
            if (event.key === 'Escape') {
                widget.classList.remove('is-open');
                trigger.focus();
            }
        });

        select.addEventListener('change', function () {
            triggerText.textContent = getSelectedText(select);
            renderOptions(select, optionsBox, triggerText, search.value);
        });

        renderOptions(select, optionsBox, triggerText, '');
    }

    document.addEventListener('click', function (event) {
        if (!event.target.closest('.app-searchable-select')) {
            closeAll();
        }
    });

    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('select[data-searchable-select]').forEach(enhance);
    });
}());
