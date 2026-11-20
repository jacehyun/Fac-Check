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
| Support and outputs | Gemini FAQ chatbot, SMTP email, xhtml2pdf |

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
| `EMAIL_HOST_PASSWORD` | SMTP password or SMTP key from your email provider |
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
