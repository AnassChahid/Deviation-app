(function () {
    const menu = document.querySelector('.app-notification-menu[data-live-url]');
    if (!menu) {
        return;
    }

    const liveUrl = menu.dataset.liveUrl;
    const readUrlTemplate = menu.dataset.readUrlTemplate || '';
    const notificationsUrl = menu.dataset.notificationsUrl || '/notifications';
    const csrfToken = menu.dataset.csrfToken || '';
    const dropdownItems = menu.querySelector('.app-notification-items');
    let requestInFlight = false;

    function readUrl(notificationId) {
        const replacement = `/${encodeURIComponent(notificationId)}/read`;
        return readUrlTemplate.replace(/\/0\/read$/, replacement) || readUrlTemplate;
    }

    function setBadge(selector, count, createBadge) {
        let badge = document.querySelector(selector);

        if (!count) {
            if (badge) {
                badge.remove();
            }
            return;
        }

        if (!badge) {
            badge = createBadge();
        }

        badge.textContent = count;
    }

    function updateBadges(unread) {
        const count = Number(unread) || 0;

        setBadge('.app-notification-toggle .app-notification-badge', count, function () {
            const toggle = menu.querySelector('.app-notification-toggle');
            const badge = document.createElement('span');
            badge.className = 'app-notification-badge';
            toggle.appendChild(badge);
            return badge;
        });

        setBadge('.app-notification-sidebar-badge', count, function () {
            const navLinks = document.querySelectorAll('.pcoded-navbar a.nav-link');
            let navText = null;

            for (let index = 0; index < navLinks.length; index += 1) {
                const href = navLinks[index].getAttribute('href') || '';
                if (href === notificationsUrl || href.endsWith('/notifications')) {
                    navText = navLinks[index].querySelector('.pcoded-mtext');
                    break;
                }
            }

            const badge = document.createElement('span');
            badge.className = 'pcoded-badge badge badge-danger app-notification-sidebar-badge';
            if (navText && navText.parentElement) {
                navText.parentElement.appendChild(badge);
            }
            return badge;
        });
    }

    function createHiddenInput(name, value) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = name;
        input.value = value;
        return input;
    }

    function createNotificationItem(notification) {
        const form = document.createElement('form');
        form.method = 'post';
        form.action = readUrl(notification.id);

        if (csrfToken) {
            form.appendChild(createHiddenInput('csrf_token', csrfToken));
        }

        if (notification.deviation_id) {
            form.appendChild(createHiddenInput('deviation_id', notification.deviation_id));
        }

        const button = document.createElement('button');
        button.type = 'submit';
        button.className = `app-notification-item${notification.read ? '' : ' is-unread'}`;

        const title = document.createElement('span');
        title.textContent = notification.title || 'Notification';

        const message = document.createElement('small');
        message.textContent = notification.message || '';

        button.appendChild(title);
        button.appendChild(message);
        form.appendChild(button);
        return form;
    }

    function renderDropdown(notifications) {
        if (!dropdownItems) {
            return;
        }

        dropdownItems.replaceChildren();

        if (!notifications.length) {
            const empty = document.createElement('div');
            empty.className = 'app-notification-empty';
            empty.textContent = 'No notifications';
            dropdownItems.appendChild(empty);
            return;
        }

        notifications.forEach(function (notification) {
            dropdownItems.appendChild(createNotificationItem(notification));
        });
    }

    function refreshNotifications() {
        if (requestInFlight) {
            return;
        }

        requestInFlight = true;

        fetch(liveUrl, {
            headers: {
                'Accept': 'application/json',
            },
            credentials: 'same-origin',
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error('Notification refresh failed');
                }
                return response.json();
            })
            .then(function (payload) {
                updateBadges(payload.unread);
                renderDropdown(payload.notifications || []);
            })
            .catch(function () {
                // Keep the server-rendered notifications if the live refresh fails.
            })
            .finally(function () {
                requestInFlight = false;
            });
    }

    refreshNotifications();
    window.setInterval(refreshNotifications, 5000);
}());
