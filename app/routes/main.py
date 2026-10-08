"""Public pages + authentication (home, jobs, login, register, dashboard redirect)."""
from datetime import date

from flask import (render_template, request, redirect, url_for, flash)
from flask_login import (login_user, logout_user, login_required, current_user)
from sqlalchemy import or_

from app import app
from app.extensions import db
from app.constants import INTERVIEW_TYPES, JOB_TYPES, STATUSES, STATUS_COLORS
from app.models import Application, Category, Company, Employer, Job, JobSeeker, User
from app.helpers import current_seeker, open_jobs_query
from app.matching import calculate_match


@app.context_processor
def inject_globals():
    unread = 0
    if current_user.is_authenticated:
        unread = current_user.notifications.filter_by(is_read=False).count()
    return dict(unread_count=unread, STATUSES=STATUSES, JOB_TYPES=JOB_TYPES,
                INTERVIEW_TYPES=INTERVIEW_TYPES, STATUS_COLORS=STATUS_COLORS,
                today=date.today())


@app.errorhandler(403)
def forbidden(_e):
    return render_template("error.html", code=403, msg="You don't have permission to view this page."), 403


@app.errorhandler(404)
def not_found(_e):
    return render_template("error.html", code=404, msg="The page you are looking for was not found."), 404


@app.errorhandler(413)
def too_large(_e):
    flash("File too large (max 5 MB).", "danger")
    return redirect(request.referrer or url_for("home"))


@app.route("/")
def home():
    latest = open_jobs_query().order_by(Job.created_at.desc()).limit(6).all()
    stats = dict(jobs=open_jobs_query().count(),
                 companies=Company.query.count(),
                 seekers=JobSeeker.query.count())
    categories = Category.query.order_by(Category.name).all()
    return render_template("home.html", latest=latest, stats=stats, categories=categories)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role")
        company_name = request.form.get("company_name", "").strip()
        error = None
        if not name or not email or len(password) < 6:
            error = "Name, email and a password of at least 6 characters are required."
        elif role not in ("seeker", "employer"):
            error = "Please choose a role."
        elif role == "employer" and not company_name:
            error = "Company name is required for employers."
        elif User.query.filter_by(email=email).first():
            error = "That email is already registered."
        if error:
            flash(error, "danger")
        else:
            user = User(name=name, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()
            if role == "seeker":
                db.session.add(JobSeeker(user_id=user.id))
            else:
                emp = Employer(user_id=user.id)
                db.session.add(emp)
                db.session.flush()
                db.session.add(Company(employer_id=emp.id, name=company_name))
            db.session.commit()
            login_user(user)
            flash("Welcome! Your account has been created. Please complete your profile.", "success")
            return redirect(url_for("profile" if role == "seeker" else "company_profile"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(request.form.get("password", "")):
            flash("Invalid email or password.", "danger")
        elif not user.active:
            flash("Your account has been suspended. Contact the administrator.", "danger")
        else:
            login_user(user)
            nxt = request.args.get("next")
            return redirect(nxt if nxt and nxt.startswith("/") else url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "admin":
        return redirect(url_for("admin_dashboard"))
    if current_user.role == "employer":
        return redirect(url_for("employer_dashboard"))
    return redirect(url_for("seeker_dashboard"))


@app.route("/jobs")
def jobs():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", type=int)
    location = request.args.get("location", "").strip()
    job_type = request.args.get("job_type", "")
    query = open_jobs_query().join(Company)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Job.title.ilike(like), Job.description.ilike(like),
                                 Company.name.ilike(like)))
    if category:
        query = query.filter(Job.category_id == category)
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if job_type:
        query = query.filter(Job.job_type == job_type)
    page = request.args.get("page", 1, type=int)
    pagination = query.order_by(Job.created_at.desc()).paginate(page=page, per_page=9, error_out=False)
    seeker = current_seeker()
    scores = {j.id: calculate_match(j, seeker) for j in pagination.items} if seeker else {}
    return render_template("jobs.html", pagination=pagination, scores=scores,
                           categories=Category.query.order_by(Category.name).all(),
                           q=q, category=category, location=location, job_type=job_type)


@app.route("/jobs/<int:job_id>")
def job_detail(job_id):
    job = db.get_or_404(Job, job_id)
    seeker = current_seeker()
    match = calculate_match(job, seeker) if seeker else None
    applied = None
    if seeker:
        applied = Application.query.filter_by(job_id=job.id, jobseeker_id=seeker.id).first()
    return render_template("job_detail.html", job=job, match=match, applied=applied, seeker=seeker)
