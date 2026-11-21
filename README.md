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
| `EMAIL_BACKEND` | Django email backend. The default is SMTP. Set `accounts.email_backends.GmailAPIBackend` to select the Gmail API. |
| `EMAIL_FROM_ADDRESS` | Sender address for the selected backend |
| `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN` | Google OAuth client credentials and the sender account's refresh token. Required for the Gmail API backend. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | SMTP server, port, login, and password or SMTP key. Used by the SMTP backend. |

## Deploy on Render

The live Fac-Check site runs on a Render Free web service connected to this repository's `main` branch. [Open Fac-Check](https://fac-check-free.onrender.com/)

To set up another instance, create a **Python Web Service** from `main` and select **Free** during manual setup. The checked-in [Render Blueprint](render.yaml) selects the Starter plan.

| Setting | Value |
| --- | --- |
| Python version | `PYTHON_VERSION=3.13.4` |
| Build command | `bash build.sh` |
| Start command | `gunicorn -k uvicorn_worker.UvicornWorker config.asgi:application` |
| Health check path | `/auth/index/` |
| Runtime settings | `DEBUG=False`, `BEHIND_PROXY=True`, `WEB_CONCURRENCY=1` |

- Set the app variables and the settings for your chosen email backend in Render. For an existing Supabase database, use its [Session pooler connection URL](https://supabase.com/docs/guides/database/connecting-to-postgres#shared-pooler-session-mode). For Render Key Value, use the internal URL from an instance in the same region as the web service.
- Fac-Check reads the generated `.onrender.com` hostname and HTTPS URL automatically. For a custom domain, set `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `SITE_URL`.
- [`build.sh`](build.sh) installs dependencies, builds Tailwind CSS, collects static files, and runs Django migrations against `DATABASE_URL`. Back up an existing database before deploying schema changes. Before sharing the deployment, test verification email delivery, photo classification, and live notifications.

### Gmail API on Render Free

The live service sends login codes, account verification, and notifications through the Gmail API over HTTPS. Render Free blocks outbound connections on the standard SMTP ports `25`, `465`, and `587`. [Render Free networking limits](https://render.com/docs/free#other-limitations)

1. Enable the [Gmail API](https://developers.google.com/workspace/gmail/api/quickstart/python) in a Google Cloud project and create a **Desktop app** OAuth client. Choose the send-only [`gmail.send` scope](https://developers.google.com/workspace/gmail/api/auth/scopes).
2. For an External OAuth app, set its publishing status to **In production** before authorizing the sender for the live service. Google issues refresh tokens that expire after seven days for External apps in **Testing** with this scope. [Refresh token rules](https://developers.google.com/identity/protocols/oauth2#expiration)
3. Authorize the client from the account that matches `EMAIL_FROM_ADDRESS`. Use the [installed app OAuth flow](https://developers.google.com/identity/protocols/oauth2/native-app) with offline access to get a refresh token.
4. In the Render dashboard, open the web service's **Environment** page and fill in these settings. Keep the OAuth credential values in Render.


   ```dotenv
   EMAIL_BACKEND=accounts.email_backends.GmailAPIBackend
   EMAIL_FROM_ADDRESS=
   GMAIL_CLIENT_ID=
   GMAIL_CLIENT_SECRET=
   GMAIL_REFRESH_TOKEN=
   ```

5. If the Gmail backend is already deployed, choose **Save and deploy** to apply the settings to the existing build. Sign in to the live site to request a fresh login code, then confirm its sender and inbox placement. [Render environment settings](https://render.com/docs/configure-environment-variables#setting-environment-variables)

### SMTP deployments

Django loads `EMAIL_HOST_PASSWORD` for the default SMTP backend. The provider comes from `EMAIL_HOST`. To use Brevo SMTP on another Render Free deployment, set `EMAIL_HOST=smtp-relay.brevo.com`, `EMAIL_PORT=2525`, and supply the Brevo SMTP login, key, and verified sender address.

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
