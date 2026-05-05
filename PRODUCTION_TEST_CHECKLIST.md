# Production Test Checklist

Use this checklist on a staging environment that matches production before moving the app live.

## 1. Configuration

- [ ] `Backend\.env` uses a production SQL Server database, not localdb or a test database.
- [ ] `Backend\.env` has `SECRET_KEY` set to a unique strong value with at least 32 characters.
- [ ] `Backend\.env` has `ENABLE_API_DOCS=False`.
- [ ] `Backend\.env` has `AUTO_CREATE_DATABASE=False`.
- [ ] `Backend\.env` has `RUN_STARTUP_MIGRATIONS=False`.
- [ ] `Frontend\.env` has `DEBUG=False`.
- [ ] `Frontend\.env` has `FLASK_DEBUG=0`.
- [ ] `Frontend\.env` has a unique strong `SECRET_KEY`.
- [ ] `Frontend\.env` has `BACKEND_API_URL` pointing to the deployed backend URL.
- [ ] `.env` files are not committed to git.
- [ ] Runtime logs are not committed to git.

## 2. Backend Health

Run:

```powershell
Invoke-RestMethod http://<backend-host>:8001/health
Invoke-RestMethod http://<backend-host>:8001/health/db
```

Expected:

- [ ] `/health` returns `status: ok`.
- [ ] `/health/db` returns `database: reachable`.
- [ ] `/docs`, `/redoc`, and `/openapi.json` are not publicly available when `ENABLE_API_DOCS=False`.

## 3. First Admin

- [ ] Start with a controlled migrated database; do not rely on app startup to change schema.
- [ ] Create the first admin using the register page or `POST /auth/bootstrap-admin`.
- [ ] Confirm the first admin can log in.
- [ ] Confirm a second call to `/auth/bootstrap-admin` is rejected.

## 4. User Approval Flow

- [ ] Register a normal user with an `@apmterminals.com` email.
- [ ] Confirm the new user cannot log in before activation.
- [ ] Log in as admin.
- [ ] Activate the new user from Manage Users.
- [ ] Confirm the activated user can log in.
- [ ] Confirm a non-company email cannot register.

## 5. Reference Data

As admin/superuser:

- [ ] Create or verify at least one deviation type.
- [ ] Create or verify at least one vessel.
- [ ] Create or verify at least one QC.
- [ ] Confirm inactive deviation types do not appear in normal deviation forms.

## 6. Deviation Workflow

As a normal user:

- [ ] Create a deviation with date, shift, area, status, deviation type, QC, vessel, and description.
- [ ] Confirm the deviation appears in the user deviation list.
- [ ] Edit the deviation.
- [ ] Set status to `Done`.
- [ ] Open the deviation detail page.
- [ ] Confirm the audit trail shows create/update/close actions.

As admin/superuser:

- [ ] Confirm admin can see the normal user's deviation.
- [ ] Confirm dashboard counts update.
- [ ] Confirm filters work on Deviations.
- [ ] Confirm pagination and search work.

## 7. Notifications

Use two browsers or two profiles:

- [ ] Browser A: log in as admin/superuser.
- [ ] Browser B: log in as normal user.
- [ ] Browser B: create a deviation.
- [ ] Browser A: refresh the page.
- [ ] Confirm the notification bell shows an unread badge.
- [ ] Open Notifications.
- [ ] Confirm the notification links to the new deviation.
- [ ] Browser B: edit the deviation.
- [ ] Browser A: confirm an update notification appears.
- [ ] Browser B: delete a deviation.
- [ ] Browser A: confirm a delete notification appears and can be marked read.
- [ ] Mark the notification read.
- [ ] Confirm unread count decreases.

## 8. Authorization And Session

- [ ] Normal user cannot access Manage Users.
- [ ] Normal user cannot create deviation types.
- [ ] Normal user cannot manage vessels.
- [ ] Expired or invalid backend token causes frontend logout.
- [ ] Logout clears the session and returns to login.

## 9. Browser And Layout

Test at minimum:

- [ ] Chrome desktop.
- [ ] Edge desktop.
- [ ] Mobile-width browser viewport.

Check:

- [ ] Sidebar expanded state.
- [ ] Sidebar collapsed state.
- [ ] Header user menu.
- [ ] Notification dropdown.
- [ ] Login/register pages.
- [ ] Tables do not overlap important controls.

## 10. Production Start

- [ ] Backend runs without `--reload`.
- [ ] Backend is started with `Backend\start-production.ps1` or an equivalent no-reload command.
- [ ] Frontend is started with `Frontend\start-production.ps1` or an equivalent WSGI server command.
- [ ] Frontend runs behind a production process manager or reverse proxy.
- [ ] HTTPS is enabled.
- [ ] HTTP redirects to HTTPS.
- [ ] Server restart brings both apps back online.
- [ ] Database backup plan is confirmed.

## Release Decision

Only move to production when every required item above passes or has an explicitly accepted owner/risk.
