"""Employer routes: company profile, jobs, applicants, status changes, interviews."""
from datetime import datetime

from flask import (render_template, request, redirect, url_for, flash, abort)
from flask_login import current_user

from app import app
from app.extensions import db
from app.constants import INTERVIEW_TYPES, JOB_TYPES, STATUSES
from app.models import Application, Category, Interview, Job, Skill
from app.helpers import employer_owns, notify, parse_date, role_required, skills_from_form, to_int
from app.matching import calculate_match


@app.route("/employer/dashboard")
@role_required("employer")
def employer_dashboard():
    company = current_user.employer.company
    my_jobs = sorted(company.jobs, key=lambda j: j.created_at, reverse=True)
    apps = (Application.query.join(Job).filter(Job.company_id == company.id)
            .order_by(Application.applied_at.desc()).all())
    stats = dict(jobs=len(my_jobs), apps=len(apps),
                 new=sum(1 for a in apps if a.status == "Applied"),
                 shortlisted=sum(1 for a in apps if a.status == "Shortlisted"),
                 interviews=sum(1 for a in apps if a.interview))
    return render_template("employer_dashboard.html", company=company, jobs=my_jobs,
                           recent=apps[:6], stats=stats)


@app.route("/employer/company", methods=["GET", "POST"])
@role_required("employer")
def company_profile():
    employer = current_user.employer
    company = employer.company
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Company name is required.", "danger")
        else:
            company.name = name
            company.industry = request.form.get("industry", "").strip()
            company.location = request.form.get("location", "").strip()
            company.website = request.form.get("website", "").strip()
            company.description = request.form.get("description", "").strip()
            employer.phone = request.form.get("phone", "").strip()
            employer.position = request.form.get("position", "").strip()
            db.session.commit()
            flash("Company profile saved.", "success")
            return redirect(url_for("company_profile"))
    return render_template("company_profile.html", company=company, employer=employer)


def fill_job_from_form(job, form, editing=False):
    """Copy form data into a Job. Returns an error message or None."""
    title = form.get("title", "").strip()
    description = form.get("description", "").strip()
    if not title or not description:
        return "Title and description are required."
    job.title = title
    job.description = description
    job.requirements = form.get("requirements", "").strip()
    job.category_id = to_int(form.get("category_id")) or None
    job.location = form.get("location", "").strip()
    job.job_type = form.get("job_type") if form.get("job_type") in JOB_TYPES else "Full-time"
    job.salary = form.get("salary", "").strip()
    job.experience_required = to_int(form.get("experience_required"))
    job.deadline = parse_date(form.get("deadline"))
    job.is_active = ("is_active" in form) if editing else True
    job.skills = skills_from_form(form)
    return None


@app.route("/employer/jobs/new", methods=["GET", "POST"])
@role_required("employer")
def job_new():
    job = Job(company_id=current_user.employer.company.id)
    if request.method == "POST":
        error = fill_job_from_form(job, request.form)
        if error:
            flash(error, "danger")
        else:
            db.session.add(job)
            db.session.commit()
            flash("Job posted!", "success")
            return redirect(url_for("employer_dashboard"))
    return render_template("job_form.html", job=job, editing=False,
                           categories=Category.query.order_by(Category.name).all(),
                           all_skills=Skill.query.order_by(Skill.name).all())


@app.route("/employer/jobs/<int:job_id>/edit", methods=["GET", "POST"])
@role_required("employer")
def job_edit(job_id):
    job = db.get_or_404(Job, job_id)
    if not employer_owns(job):
        abort(403)
    if request.method == "POST":
        error = fill_job_from_form(job, request.form, editing=True)
        if error:
            flash(error, "danger")
        else:
            db.session.commit()
            flash("Job updated.", "success")
            return redirect(url_for("employer_dashboard"))
    return render_template("job_form.html", job=job, editing=True,
                           categories=Category.query.order_by(Category.name).all(),
                           all_skills=Skill.query.order_by(Skill.name).all())


@app.route("/employer/jobs/<int:job_id>/delete", methods=["POST"])
@role_required("employer")
def job_delete(job_id):
    job = db.get_or_404(Job, job_id)
    if not employer_owns(job):
        abort(403)
    db.session.delete(job)
    db.session.commit()
    flash("Job deleted.", "info")
    return redirect(url_for("employer_dashboard"))


@app.route("/employer/applicants")
@role_required("employer")
def applicants():
    company = current_user.employer.company
    job_id = request.args.get("job_id", type=int)
    status = request.args.get("status", "")
    sort = request.args.get("sort", "score")
    query = Application.query.join(Job).filter(Job.company_id == company.id)
    if job_id:
        query = query.filter(Job.id == job_id)
    if status in STATUSES:
        query = query.filter(Application.status == status)
    order = Application.match_score.desc() if sort == "score" else Application.applied_at.desc()
    return render_template("applicants.html", apps=query.order_by(order).all(),
                           jobs=company.jobs, job_id=job_id, status=status, sort=sort)


def get_employer_application(app_id):
    application = db.get_or_404(Application, app_id)
    if not employer_owns(application.job):
        abort(403)
    return application


@app.route("/employer/applications/<int:app_id>")
@role_required("employer")
def applicant_detail(app_id):
    application = get_employer_application(app_id)
    match = calculate_match(application.job, application.jobseeker)
    return render_template("applicant_detail.html", a=application, match=match)


@app.route("/employer/applications/<int:app_id>/status", methods=["POST"])
@role_required("employer")
def application_status(app_id):
    application = get_employer_application(app_id)
    status = request.form.get("status")
    if status not in STATUSES:
        abort(400)
    if status != application.status:
        application.status = status
        job = application.job
        verb = "shortlisted" if status == "Shortlisted" else f"updated to '{status}'"
        notify(application.jobseeker.user_id,
               f"Your application for {job.title} at {job.company.name} was {verb}.",
               url_for("my_applications"))
        db.session.commit()
        flash(f"Status changed to {status}.", "success")
    return redirect(request.referrer or url_for("applicants"))


@app.route("/employer/applications/<int:app_id>/interview", methods=["POST"])
@role_required("employer")
def schedule_interview(app_id):
    application = get_employer_application(app_id)
    try:
        when = datetime.strptime(f"{request.form.get('date')} {request.form.get('time')}",
                                 "%Y-%m-%d %H:%M")
    except ValueError:
        flash("Please enter a valid date and time.", "danger")
        return redirect(url_for("applicant_detail", app_id=app_id))
    itv = application.interview or Interview(application=application)
    itv.scheduled_at = when
    itv.interview_type = request.form.get("interview_type") if request.form.get("interview_type") in INTERVIEW_TYPES else "Online"
    itv.location_link = request.form.get("location_link", "").strip()
    itv.notes = request.form.get("notes", "").strip()
    db.session.add(itv)
    application.status = "Interview"
    job = application.job
    notify(application.jobseeker.user_id,
           f"Interview scheduled for {job.title} at {job.company.name} on "
           f"{when.strftime('%d %b %Y, %H:%M')}.", url_for("interviews"))
    db.session.commit()
    flash("Interview scheduled and the candidate was notified.", "success")
    return redirect(url_for("applicant_detail", app_id=app_id))
