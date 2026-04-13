# WE Gold Dashboard - Django

Server-rendered Arabic dashboard for managing WE Gold primary lines, members, renewals, and accounting.

## Stack

- Django 5.2
- Django Templates
- Whitenoise (static files in production)
- Gunicorn (WSGI server)

## Structure

- `config/`: Django project settings and root URLs
- `dashboard/`: App models, views, forms, tests
- `templates/dashboard/home.html`: Main dashboard page
- `static/dashboard/style.css`: Shared custom styling

## Local Development

1. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

2. Apply database migrations:

```bash
python manage.py migrate
```

3. Start local server:

```bash
python manage.py runserver
```

## Production Preparation

1. Create your environment file from `.env.example` and set real values:

- `DJANGO_SECRET_KEY`: strong secret key
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS`: your real domains
- `DJANGO_CSRF_TRUSTED_ORIGINS`: HTTPS origins only
- `DATABASE_URL`: preferably PostgreSQL in production

2. Install dependencies in production:

```bash
python -m pip install -r requirements.txt
```

3. Apply migrations:

```bash
python manage.py migrate
```

4. Collect static files:

```bash
python manage.py collectstatic --noinput
```

5. Run app with Gunicorn:

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

`Procfile` is included for platforms like Render/Heroku style deployments.

## Deployment Checklist

- Keep `DJANGO_SECRET_KEY` private
- Keep `DJANGO_DEBUG=False`
- Configure `ALLOWED_HOSTS` and trusted origins
- Use HTTPS and reverse proxy
- Use managed PostgreSQL for production data
- Run periodic backups for database

## Deploy On Vercel

This project is already prepared with `vercel.json`.

1. Push your project to GitHub.
2. In Vercel, create a new project and import this repository.
3. In Vercel Project Settings -> Environment Variables, add:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS=.vercel.app`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://*.vercel.app`
- `DATABASE_URL` (recommended: managed PostgreSQL)
- `DJANGO_DB_SSL_REQUIRE=True`

Suggested values to paste quickly:

```env
DJANGO_SECRET_KEY=replace-with-strong-secret
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=.vercel.app
DJANGO_CSRF_TRUSTED_ORIGINS=https://*.vercel.app
DATABASE_URL=postgres://USER:PASSWORD@HOST:5432/DBNAME
DJANGO_DB_SSL_REQUIRE=True
DJANGO_STATICFILES_STORAGE=whitenoise.storage.CompressedStaticFilesStorage
DJANGO_WHITENOISE_USE_FINDERS=True
```

4. Deploy.

After first deploy, if you use a fresh DB, run migrations:

```bash
python manage.py migrate
```
