# Kiambu Road School — Management System

A full-featured school management system built with **Django** and **SQLite**, featuring a modern dashboard UI.

## Features

- **Dashboard** — Students, teachers, attendance, and fee overview
- **Students** — Registration, profiles, class assignment, search & filter
- **Teachers** — Staff directory with subject assignments
- **Classrooms** — Grade sections with homeroom teachers
- **Subjects** — Curriculum management
- **Timetable** — Weekly schedule per class
- **Attendance** — Daily class attendance marking
- **Exams & Grades** — Exam scheduling and grade entry with letter grades
- **Fees** — Tuition tracking (pending, paid, partial, overdue)
- **Report cards** — View, print, and download student report cards as PDF
- **Settings** — Academic years and grade levels (admin only)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Load demo data and admin account
python manage.py setup_demo

# Start the development server
python manage.py runserver
```

Open **http://127.0.0.1:8000/** and sign in with:

| Role | Username | Password |
|------|----------|----------|
| Administrator | `admin` | `admin123` |
| Teacher | `sarah.johnson` | `teacher123` |
| Teacher | `michael.chen` | `teacher123` |
| Teacher | `emily.davis` | `teacher123` |
| Teacher | `james.wilson` | `teacher123` |

Students and guardians do not have login accounts — they are managed by staff only.

## Tech Stack

- Django 5.x
- SQLite (default database)
- Bootstrap 5 + custom CSS (Plus Jakarta Sans)

## Project Structure

```
schoolmgmt/     # Project settings
school/         # Main application (models, views, templates)
static/         # Global CSS
manage.py
db.sqlite3      # Created after migrate
```

## Django Admin

Visit `/admin/` after creating a superuser:

```bash
python manage.py createsuperuser
```

## Deploy on Render

This project uses **SQLite** (no separate database service). The [Render Blueprint](https://render.com/docs/blueprint-spec) (`render.yaml`) creates only a free web service.

> **Note:** On Render’s free tier, the filesystem is reset on each deploy, so SQLite data is recreated when you redeploy. Keep `LOAD_DEMO_DATA=true` to reload sample data automatically, or back up `db.sqlite3` if you need to preserve data.

### Option A — Blueprint (recommended)

1. Push this project to a GitHub repository.
2. Go to [Render Dashboard](https://dashboard.render.com/) → **New** → **Blueprint**.
3. Connect your repo and apply the blueprint.
4. Wait for the build to finish, then open your app URL.

Default logins after the first deploy (demo data is loaded automatically):

| Role | Username | Password |
|------|----------|----------|
| Administrator | `admin` | `admin123` |
| Teacher | `sarah.johnson` | `teacher123` |
| Teacher | `michael.chen` | `teacher123` |
| Teacher | `emily.davis` | `teacher123` |
| Teacher | `james.wilson` | `teacher123` |

After your first successful deploy, set `LOAD_DEMO_DATA` to `false` if you add your own data and want redeploys to keep it (until the next full redeploy wipes the disk).

### Option B — Manual web service

1. Create a **Web Service**, connect your repo, and use:

| Setting | Value |
|---------|-------|
| **Build Command** | `./build.sh` |
| **Start Command** | `gunicorn schoolmgmt.wsgi:application` |
| **Health Check Path** | `/login/` |

2. Add environment variables:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | A long random string |
| `DEBUG` | `False` |
| `LOAD_DEMO_DATA` | `true` (loads demo data on each deploy) |
| `PYTHON_VERSION` | `3.12.0` |

Render sets `RENDER_EXTERNAL_HOSTNAME` automatically for `ALLOWED_HOSTS` and CSRF.

### Local production check

```bash
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
gunicorn schoolmgmt.wsgi:application
```
