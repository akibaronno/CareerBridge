from datetime import datetime, date

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db, login_manager


# Many-to-many link tables
job_skills = db.Table(
    "job_skills",
    db.Column("job_id", db.Integer, db.ForeignKey("jobs.id"), primary_key=True),
    db.Column("skill_id", db.Integer, db.ForeignKey("skills.id"), primary_key=True),
)
jobseeker_skills = db.Table(
    "jobseeker_skills",
    db.Column("jobseeker_id", db.Integer, db.ForeignKey("jobseekers.id"), primary_key=True),
    db.Column("skill_id", db.Integer, db.ForeignKey("skills.id"), primary_key=True),
)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)          # seeker | employer | admin
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    jobseeker = db.relationship("JobSeeker", backref="user", uselist=False,
                                cascade="all, delete-orphan")
    employer = db.relationship("Employer", backref="user", uselist=False,
                               cascade="all, delete-orphan")
    notifications = db.relationship("Notification", backref="user", lazy="dynamic",
                                    cascade="all, delete-orphan")

    @property
    def is_active(self):  # Flask-Login uses this to block suspended users
        return bool(self.active)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)


class JobSeeker(db.Model):
    __tablename__ = "jobseekers"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    phone = db.Column(db.String(30))
    location = db.Column(db.String(100))
    headline = db.Column(db.String(150))
    bio = db.Column(db.Text)
    education = db.Column(db.Text)
    experience_years = db.Column(db.Integer, default=0)

    skills = db.relationship("Skill", secondary=jobseeker_skills, backref="seekers")
    cvs = db.relationship("CV", backref="jobseeker", cascade="all, delete-orphan")
    applications = db.relationship("Application", backref="jobseeker",
                                   cascade="all, delete-orphan")


class Employer(db.Model):
    __tablename__ = "employers"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    phone = db.Column(db.String(30))
    position = db.Column(db.String(100))
    company = db.relationship("Company", backref="employer", uselist=False,
                              cascade="all, delete-orphan")


class Company(db.Model):
    __tablename__ = "companies"
    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey("employers.id"), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    industry = db.Column(db.String(100))
    location = db.Column(db.String(100))
    website = db.Column(db.String(200))
    description = db.Column(db.Text)
    jobs = db.relationship("Job", backref="company", cascade="all, delete-orphan")


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    jobs = db.relationship("Job", backref="category")


class Skill(db.Model):
    __tablename__ = "skills"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)


class Job(db.Model):
    __tablename__ = "jobs"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    location = db.Column(db.String(100))
    job_type = db.Column(db.String(30), default="Full-time")
    salary = db.Column(db.String(100))
    experience_required = db.Column(db.Integer, default=0)
    deadline = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    skills = db.relationship("Skill", secondary=job_skills, backref="jobs")
    applications = db.relationship("Application", backref="job", cascade="all, delete-orphan")

    @property
    def is_open(self):
        return bool(self.is_active) and (self.deadline is None or self.deadline >= date.today())


class CV(db.Model):
    __tablename__ = "cvs"
    id = db.Column(db.Integer, primary_key=True)
    jobseeker_id = db.Column(db.Integer, db.ForeignKey("jobseekers.id"), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class Application(db.Model):
    __tablename__ = "applications"
    __table_args__ = (db.UniqueConstraint("job_id", "jobseeker_id", name="uq_job_seeker"),)
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    jobseeker_id = db.Column(db.Integer, db.ForeignKey("jobseekers.id"), nullable=False)
    cv_id = db.Column(db.Integer, db.ForeignKey("cvs.id"))
    cover_letter = db.Column(db.Text)
    status = db.Column(db.String(30), default="Applied")
    match_score = db.Column(db.Integer, default=0)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    cv = db.relationship("CV")
    interview = db.relationship("Interview", backref="application", uselist=False,
                                cascade="all, delete-orphan")


class Interview(db.Model):
    __tablename__ = "interviews"
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"),
                               unique=True, nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    interview_type = db.Column(db.String(30), default="Online")
    location_link = db.Column(db.String(255))
    notes = db.Column(db.Text)


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))