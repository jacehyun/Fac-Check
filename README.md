# Fac-Check

Fac-Check is a facility concern reporting and corrective maintenance management system built as a 2026 BS Information Technology capstone project for Universidad de Manila. It gives students, faculty, and staff a place to report campus facility concerns and track their progress. The university's Maintenance and Engineering Division (MED) uses the same system to review reports, assign work, and maintain a record of corrective maintenance.

## How it works

1. A campus user submits a concern with a photo, a location, and a description.
2. A MobileNetV2-based convolutional neural network (CNN) suggests a maintenance category from the photo. Fac-Check flags uncertain predictions for manual review.
3. MED administrators verify the report, set its priority, assign personnel, and manage the linked Job Order. Reports move through **Pending**, **In Progress**, **Resolved**, and **Closed**.
4. Users receive in-app and email updates. The Client Satisfaction Survey records ratings for Quality, Quantity, and Timeliness.

The administrative dashboard shows report trends and resolution times. Administrators can generate Job Order PDFs and export maintenance records. Campus users can access a chatbot for frequently asked questions.

### Photo classification

The deployed application uses a TensorFlow/Keras model. Its [seven categories](ml/class_labels.json) cover carpentry and masonry, electrical, others, painting, plumbing, refrigeration and air conditioning units, and vehicle check-up. The [inference configuration](ml/inference_config.json) defines when to flag an image for review.

## Tech stack

| Area | Technology |
| --- | --- |
| Web application | Python 3.13, Django 6, Tailwind CSS, JavaScript |
| Data and uploads | PostgreSQL, Cloudinary |
| Live notifications | Django Channels and Redis |
| Photo classification | TensorFlow and Keras |
| Support and outputs | Gemini FAQ chatbot, SMTP or Gmail API email, xhtml2pdf |

## Run locally

Install Python 3.13, Node.js with npm, and PostgreSQL or get a development PostgreSQL connection URL. Clone this repository, then create and activate a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

In PowerShell, activate the virtual environment with `& .\.venv\Scripts\Activate.ps1` and copy the template with `Copy-Item .env.example .env`.

Fill in your local `.env` using the [environment variable reference](#environment-variables). Use `DEBUG=True` for local development. With that setting, live notifications can use an in-memory channel layer when `REDIS_URL` is unset.

```bash
python manage.py tailwind install
python manage.py tailwind build
python manage.py migrate
python manage.py check
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Run `python manage.py createsuperuser` if you need a local administrator account.

### Environment variables

Start with [`.env.example`](.env.example). Keep actual credentials in your local `.env` or in the hosting provider's environment settings.

| Variable | Value |
| --- | --- |
| `SECRET_KEY` | A unique Django secret for the environment |
| `DATABASE_URL` | PostgreSQL connection URL |
| `REDIS_URL` | Redis-compatible connection URL, required when `DEBUG=False` |
| `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` | Cloudinary credentials for uploaded media |
| `GEMINI_API_KEY` | Key for the FAQ chatbot |
| `EMAIL_HOST_PASSWORD` | SMTP password or SMTP key when using the default SMTP backend |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_FROM_ADDRESS` | SMTP endpoint, login, and verified sender address. The defaults are for Gmail. |

## Deploy on Render

Create a **Python Web Service** from this repository's `main` branch. For a Free deployment, select **Free** during manual setup. The checked-in [Render Blueprint](render.yaml) selects the Starter plan.

| Setting | Value |
| --- | --- |
| Python version | `PYTHON_VERSION=3.13.4` |
| Build command | `bash build.sh` |
| Start command | `gunicorn -k uvicorn_worker.UvicornWorker config.asgi:application` |
| Health check path | `/auth/index/` |
| Runtime settings | `DEBUG=False`, `BEHIND_PROXY=True`, `WEB_CONCURRENCY=1` |

- Set the environment variables above in Render. For an existing Supabase database, use its [Session pooler connection URL](https://supabase.com/docs/guides/database/connecting-to-postgres#shared-pooler-session-mode). For Render Key Value, use the internal URL from an instance in the same region as the web service.
- For Brevo on Render Free, set `EMAIL_HOST=smtp-relay.brevo.com` and `EMAIL_PORT=2525`. Use the Brevo SMTP login, SMTP key, and verified sender address for the corresponding email variables.
- Fac-Check reads the generated `.onrender.com` hostname and HTTPS URL automatically. For a custom domain, set `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `SITE_URL`.
- [`build.sh`](build.sh) installs dependencies, builds Tailwind CSS, collects static files, and runs Django migrations against `DATABASE_URL`. Back up an existing database before deploying schema changes. Before sharing the deployment, test verification email delivery, photo classification, and live notifications.

### Use Gmail on Render Free

Render Free blocks outbound Gmail SMTP ports. Use the Gmail API over HTTPS to send from the Fac-Check Gmail account.

1. Enable the [Gmail API](https://developers.google.com/workspace/gmail/api/quickstart/python) in a Google Cloud project and create a **Desktop app** OAuth client. Choose the send-only [`gmail.send` scope](https://developers.google.com/workspace/gmail/api/auth/scopes).
2. Authorize the client from the Fac-Check sender account using the [installed app OAuth flow](https://developers.google.com/identity/protocols/oauth2/native-app) with offline access. Store the resulting refresh token privately alongside the client ID and secret. Google issues refresh tokens that expire after seven days for External projects in Testing mode with this scope. [Refresh token rules](https://developers.google.com/identity/protocols/oauth2#expiration)
3. Test mail from the sender account before changing the live service. When ready, set the following values in Render's Environment settings and deploy.

```dotenv
EMAIL_BACKEND=accounts.email_backends.GmailAPIBackend
EMAIL_FROM_ADDRESS=facchecknoreply@gmail.com
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REFRESH_TOKEN=
```

The Gmail account granting access must match `EMAIL_FROM_ADDRESS`. Keep secrets in Render's environment settings or a private local `.env`.

## Repository layout

| Path | Contents |
| --- | --- |
| [`accounts/`](accounts/) | Registration, sign-in, email verification, and account recovery |
| [`user/`](user/) | Concern submission, status tracking, surveys, and notifications |
| [`adm/`](adm/) | MED dashboard, Job Orders, personnel, and maintenance records |
| [`ml/`](ml/) | Keras model, inference code, and category configuration |
| [`theme/`](theme/) | Shared templates and Tailwind source |
| [`config/`](config/) | Django settings, routing, and ASGI entry point |

## Contributing

Use a focused branch and keep changes reviewable. Test migrations before sharing them, rebuild Tailwind after styling changes, and update this README when setup or deployment steps change.
