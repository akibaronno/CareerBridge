# CareerBridge

A full-stack **job recruitment and career portal** where job seekers find and apply for jobs, employers post vacancies and manage applicants, and admins keep the platform running. Its standout feature is **skill-based matching**: every job shows how well a candidate's skills fit, and seekers get personalised job recommendations.

🌐 **Live demo:** https://careerbridge-bqle.onrender.com/

> The demo runs on a free Render instance, so the first load may take up to a minute while the server wakes up.

---

## Features

### Job Seekers
- Register and build a profile (headline, bio, education, experience, location, skills)
- Upload, download and delete CVs (PDF, DOC, DOCX, max 5 MB)
- Search and filter jobs by keyword, category, location and job type
- See a **match score** on every job, with matched and missing skills
- Get **recommended jobs** ranked by how well they fit
- Apply with a CV and cover letter, and track application status
- View scheduled interviews and receive in-app notifications

### Employers
- Register with a company and manage the company profile
- Post, edit and delete jobs with required skills, salary, experience and deadline
- View applicants per job, each with their match score, CV and cover letter
- Move applicants through the hiring pipeline:
  `Applied → Under Review → Shortlisted → Interview → Selected / Rejected`
- Schedule interviews (Online, On-site or Phone) with a link or location and notes
- Candidates are notified automatically on status changes and interviews

### Admin
- Dashboard with platform statistics (users, jobs, applications, interviews, status breakdown)
- Suspend or reactivate user accounts
- Activate, deactivate or delete any job
- Manage job categories and the skills list

### Skill Matching

```
match score = (required skills the candidate has ÷ total required skills) × 100
```

The result also lists the **matched** and **missing** skills. The score is saved with each application so employers can rank applicants at a glance.

---

## Tech Stack

| Layer      | Technology                                   |
|------------|----------------------------------------------|
| Backend    | Python, Flask                                |
| Database   | MySQL, Flask-SQLAlchemy (PyMySQL driver)     |
| Auth       | Flask-Login, Werkzeug password hashing       |
| Frontend   | Jinja2 templates, HTML, CSS, JavaScript, Bootstrap 5 |
| Deployment | Render (Gunicorn)                            |

---

## Project Structure

```
CareerBridge/
├── app/
│   ├── __init__.py        # Creates the Flask app
│   ├── extensions.py      # db and login manager
│   ├── models.py          # Database models
│   ├── matching.py        # Match score + job recommendations
│   ├── helpers.py         # Role guard, notifications, form helpers
│   ├── constants.py       # Statuses, job types, allowed CV types
│   ├── seed.py            # Creates tables and seeds default data
│   ├── routes/
│   │   ├── main.py        # Home, auth, job search and detail
│   │   ├── seeker.py      # Profile, CVs, applications, interviews, notifications
│   │   ├── employer.py    # Company, jobs, applicants, interviews
│   │   ├── admin.py       # Users, jobs, categories and skills
│   │   └── api.py         # JSON REST API
│   └── templates/         # Jinja2 HTML templates
├── uploads/               # Uploaded CVs
├── config.py              # App configuration
├── init_db.py             # One-off database setup script
├── run.py                 # Local entry point
└── requirements.txt
```

### Database Models

`User` · `JobSeeker` · `Employer` · `Company` · `Category` · `Skill` · `Job` · `CV` · `Application` · `Interview` · `Notification`

Jobs and job seekers are linked to skills through many-to-many tables, and each seeker can apply to a job only once.

---

## Getting Started

### Prerequisites
- Python 3.10+
- A MySQL server

### 1. Clone and install

```bash
git clone https://github.com/<your-username>/CareerBridge.git
cd CareerBridge

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure environment variables

| Variable       | Description                                              |
|----------------|----------------------------------------------------------|
| `DATABASE_URL` | MySQL connection string (required)                       |
| `SECRET_KEY`   | Secret used to sign sessions (set a long random value)   |

```bash
# macOS / Linux
export DATABASE_URL="mysql+pymysql://USER:PASSWORD@localhost:3306/careerbridge"
export SECRET_KEY="your-long-random-secret"

# Windows (PowerShell)
$env:DATABASE_URL="mysql+pymysql://USER:PASSWORD@localhost:3306/careerbridge"
$env:SECRET_KEY="your-long-random-secret"
```

### 3. Initialise the database

```bash
python init_db.py
```

This creates the database (if missing), all tables, default categories and skills, and the admin account.

### 4. Run the app

```bash
python run.py
```

Open http://127.0.0.1:5000.

---

## Default Admin Account

| Email             | Password    |
|-------------------|-------------|
| admin@portal.com  | Admin@123   |

⚠️ **Change this password after your first login**, especially on any public deployment.

---

## REST API

JSON endpoints are available alongside the web interface:

| Method | Endpoint                | Access  | Description                                                        |
|--------|-------------------------|---------|--------------------------------------------------------------------|
| GET    | `/api/jobs`             | Public  | List open jobs. Filters: `q`, `category`, `location`, `job_type`   |
| GET    | `/api/jobs/<id>`        | Public  | Job details (includes match data when logged in as a seeker)       |
| GET    | `/api/match/<id>`       | Seeker  | Match score, matched and missing skills for a job                  |
| GET    | `/api/recommendations`  | Seeker  | Recommended jobs ranked by match score                             |
| GET    | `/api/notifications`    | Logged in | Latest 50 notifications                                          |

Example:

```bash
curl "https://careerbridge-bqle.onrender.com/api/jobs?q=python&job_type=Full-time"
```

---

## Deployment (Render)

1. Create a MySQL database with a hosted provider and copy its connection string.
2. Create a new **Web Service** on Render from this repository.
3. Set the build command to `pip install -r requirements.txt`.
4. Set the start command to `gunicorn run:app`.
5. Add the `DATABASE_URL` and `SECRET_KEY` environment variables.
6. Run `python init_db.py` once (for example from the Render shell) to create the tables and seed data.

> Render's free tier has an ephemeral filesystem, so uploaded CVs are lost when the service restarts or redeploys. For permanent storage, use a persistent disk or an external service such as S3.

---

## Security Notes

- Passwords are hashed with Werkzeug
- Role-based access control on every protected route (seeker, employer, admin)
- Employers can only view and manage their own jobs and applicants
- Suspended accounts cannot log in
- CV uploads are limited to PDF, DOC and DOCX, up to 5 MB

---

## Future Improvements

- Email notifications
- Automatic skill extraction from uploaded CVs
- Saved jobs and job alerts
- Cloud storage for CV files

---

## Author

**Your Name**
4th-year university project

- GitHub: [@your-username](https://github.com/your-username)
- Live demo: https://careerbridge-bqle.onrender.com/
