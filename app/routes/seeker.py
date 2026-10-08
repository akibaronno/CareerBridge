"""Job seeker routes: dashboard, profile, CV, applications, interviews, notifications."""
import os
import uuid
from datetime import datetime

from flask import (render_template, request, redirect, url_for, flash, abort,
                   send_from_directory)
from flask_login import (login_required, current_user)
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from app import app
from app.extensions import db
from app.constants import STATUSES
from app.models import Application, CV, Job, Notification, Skill
from app.helpers import allowed_cv, notify, role_required, skills_from_form, to_int
from app.matching import calculate_match, recommended_jobs


@app.route("/seeker/dashboard")
@role_required("seeker")
def seeker_dashboard():
    seeker = current_user.jobseeker
    apps = sorted(seeker.applications, key=lambda a: a.applied_at, reverse=True)
    counts = {s: sum(1 for a in apps if a.status == s) for s in STATUSES}
    upcoming = [a.interview for a in apps
                if a.interview and a.interview.scheduled_at >= datetime.now()]
    upcoming.sort(key=lambda i: i.scheduled_at)
    return render_template("seeker_dashboard.html", apps=apps[:5], counts=counts,
                           total=len(apps), upcoming=upcoming[:3],
                           recs=recommended_jobs(seeker), seeker=seeker)


@app.route("/seeker/profile", methods=["GET", "POST"])
@role_required("seeker")
def profile():
    seeker = current_user.jobseeker
    if request.method == "POST":
        current_user.name = request.form.get("name", current_user.name).strip() or current_user.name
        seeker.phone = request.form.get("phone", "").strip()
        seeker.location = request.form.get("location", "").strip()
        seeker.headline = request.form.get("headline", "").strip()
        seeker.education = request.form.get("education", "").strip()
        seeker.bio = request.form.get("bio", "").strip()
        seeker.experience_years = to_int(request.form.get("experience_years"))
        seeker.skills = skills_from_form(request.form)
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("profile"))
    return render_template("seeker_profile.html", seeker=seeker,
                           all_skills=Skill.query.order_by(Skill.name).all())


@app.route("/seeker/cv/upload", methods=["POST"])
@role_required("seeker")
def cv_upload():
    file = request.files.get("cv")
    if not file or not file.filename:
        flash("Please choose a file.", "danger")
    elif not allowed_cv(file.filename):
        flash("Only PDF, DOC and DOCX files are allowed.", "danger")
    else:
        ext = file.filename.rsplit(".", 1)[1].lower()
        stored = f"{uuid.uuid4().hex}.{ext}"
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], stored))
        db.session.add(CV(jobseeker_id=current_user.jobseeker.id,
                          original_name=secure_filename(file.filename), stored_name=stored))
        db.session.commit()
        flash("CV uploaded. Delete older CVs if you want to replace them.", "success")
    return redirect(url_for("profile"))


@app.route("/cv/<int:cv_id>/download")
@login_required
def cv_download(cv_id):
    cv = db.get_or_404(CV, cv_id)
    allowed = current_user.role == "admin"
    if current_user.role == "seeker":
        allowed = cv.jobseeker_id == current_user.jobseeker.id
    elif current_user.role == "employer" and current_user.employer.company:
        # employer may download CVs attached to applications for their own jobs
        allowed = (Application.query.join(Job)
                   .filter(Application.cv_id == cv.id,
                           Job.company_id == current_user.employer.company.id).first() is not None)
    if not allowed:
        abort(403)
    return send_from_directory(app.config["UPLOAD_FOLDER"], cv.stored_name,
                               as_attachment=True, download_name=cv.original_name)


@app.route("/seeker/cv/<int:cv_id>/delete", methods=["POST"])
@role_required("seeker")
def cv_delete(cv_id):
    cv = db.get_or_404(CV, cv_id)
    if cv.jobseeker_id != current_user.jobseeker.id:
        abort(403)
    Application.query.filter_by(cv_id=cv.id).update({"cv_id": None})
    path = os.path.join(app.config["UPLOAD_FOLDER"], cv.stored_name)
    if os.path.exists(path):
        os.remove(path)
    db.session.delete(cv)
    db.session.commit()
    flash("CV deleted.", "info")
    return redirect(url_for("profile"))


@app.route("/jobs/<int:job_id>/apply", methods=["POST"])
@role_required("seeker")
def apply(job_id):
    job = db.get_or_404(Job, job_id)
    seeker = current_user.jobseeker
    cv = db.session.get(CV, to_int(request.form.get("cv_id")))
    if not job.is_open:
        flash("This job is closed.", "danger")
    elif Application.query.filter_by(job_id=job.id, jobseeker_id=seeker.id).first():
        flash("You have already applied for this job.", "warning")
    elif not cv or cv.jobseeker_id != seeker.id:
        flash("Please upload a CV in your profile and select it to apply.", "danger")
    else:
        score = calculate_match(job, seeker)["score"]
        db.session.add(Application(job_id=job.id, jobseeker_id=seeker.id, cv_id=cv.id,
                                   cover_letter=request.form.get("cover_letter", "").strip(),
                                   match_score=score))
        notify(job.company.employer.user_id,
               f"New application from {current_user.name} for {job.title} ({score}% match)",
               url_for("applicants", job_id=job.id))
        try:
            db.session.commit()
            flash("Application submitted successfully!", "success")
            return redirect(url_for("my_applications"))
        except IntegrityError:
            db.session.rollback()
            flash("You have already applied for this job.", "warning")
    return redirect(url_for("job_detail", job_id=job_id))


@app.route("/seeker/applications")
@role_required("seeker")
def my_applications():
    apps = (Application.query.filter_by(jobseeker_id=current_user.jobseeker.id)
            .order_by(Application.applied_at.desc()).all())
    return render_template("my_applications.html", apps=apps)


@app.route("/interviews")
@role_required("seeker", "employer")
def interviews():
    if current_user.role == "seeker":
        apps = Application.query.filter_by(jobseeker_id=current_user.jobseeker.id).all()
    else:
        apps = (Application.query.join(Job)
                .filter(Job.company_id == current_user.employer.company.id).all())
    items = sorted([a.interview for a in apps if a.interview], key=lambda i: i.scheduled_at)
    return render_template("interviews.html", items=items, now=datetime.now())


@app.route("/notifications")
@login_required
def notifications():
    items = current_user.notifications.order_by(Notification.created_at.desc()).limit(100).all()
    return render_template("notifications.html", items=items)


@app.route("/notifications/<int:nid>/open")
@login_required
def notification_open(nid):
    n = db.get_or_404(Notification, nid)
    if n.user_id != current_user.id:
        abort(403)
    n.is_read = True
    db.session.commit()
    return redirect(n.link or url_for("notifications"))


@app.route("/notifications/read-all", methods=["POST"])
@login_required
def notifications_read_all():
    current_user.notifications.filter_by(is_read=False).update({"is_read": True})
    db.session.commit()
    return redirect(url_for("notifications"))
