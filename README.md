# CareerBridge - Job Recruitment & Career Portal

Flask + Flask-SQLAlchemy + Flask-Login + MySQL + Bootstrap 5.

## Folder structure
```
careerbridge/
├── run.py               <- start the project here (python run.py)
├── config.py            <- DB url, secret key, upload settings
├── requirements.txt
├── uploads/             <- uploaded CVs are saved here
└── app/
    ├── __init__.py      <- creates the Flask app
    ├── extensions.py    <- db, login_manager
    ├── constants.py     <- statuses, job types, colours
    ├── models.py        <- all database tables
    ├── helpers.py       <- role_required, notify, form helpers
    ├── matching.py      <- CV-to-job match score + recommendations
    ├── seed.py          <- creates DB, default skills/categories, admin
    ├── routes/
    │   ├── main.py      <- home, jobs, login/register
    │   ├── seeker.py    <- job seeker pages
    │   ├── employer.py  <- employer pages
    │   ├── admin.py     <- admin pages
    │   └── api.py       <- REST API (JSON)
    └── templates/       <- all HTML files
```

## Run
```
python -m venv venv
venv\Scripts\activate          (Windows)   |   source venv/bin/activate  (Mac/Linux)
pip install -r requirements.txt
```
Open `config.py` and put your MySQL password in `DB_URL`, then:
```
python run.py
```
Open http://127.0.0.1:5000  -  Admin: admin@portal.com / Admin@123
