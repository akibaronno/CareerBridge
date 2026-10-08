"""Admin routes: dashboard, users, jobs, skills and categories."""

from flask import (render_template, request, redirect, url_for, flash, abort)
from flask_login import current_user
from sqlalchemy import func, or_

from app import app
from app.extensions import db
from app.constants import STATUSES
from app.models import Application, Category, Interview, Job, Skill, User
from app.helpers import open_jobs_query, role_required


@app.route("/admin")
@role_required("admin")
def admin_dashboard():
    stats = dict(users=User.query.count(),
                 seekers=User.query.filter_by(role="seeker").count(),
                 employers=User.query.filter_by(role="employer").count(),
                 suspended=User.query.filter_by(active=False).count(),
                 jobs=Job.query.count(), open_jobs=open_jobs_query().count(),
                 applications=Application.query.count(),
                 interviews=Interview.query.count())
    by_status = {s: Application.query.filter_by(status=s).count() for s in STATUSES}
    recent = User.query.order_by(User.created_at.desc()).limit(8).all()
    return render_template("admin_dashboard.html", stats=stats, by_status=by_status, recent=recent)


@app.route("/admin/users")
@role_required("admin")
def admin_users():
    role = request.args.get("role", "")
    q = request.args.get("q", "").strip()
    query = User.query
    if role in ("seeker", "employer", "admin"):
        query = query.filter_by(role=role)
    if q:
        query = query.filter(or_(User.name.ilike(f"%{q}%"), User.email.ilike(f"%{q}%")))
    return render_template("admin_users.html", users=query.order_by(User.created_at.desc()).all(),
                           role=role, q=q)


@app.route("/admin/users/<int:user_id>/toggle", methods=["POST"])
@role_required("admin")
def admin_toggle_user(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("You cannot suspend your own account.", "danger")
    else:
        user.active = not user.active
        db.session.commit()
        flash(f"{user.name} is now {'active' if user.active else 'suspended'}.", "success")
    return redirect(request.referrer or url_for("admin_users"))


@app.route("/admin/jobs")
@role_required("admin")
def admin_jobs():
    return render_template("admin_jobs.html", jobs=Job.query.order_by(Job.created_at.desc()).all())


@app.route("/admin/jobs/<int:job_id>/toggle", methods=["POST"])
@role_required("admin")
def admin_toggle_job(job_id):
    job = db.get_or_404(Job, job_id)
    job.is_active = not job.is_active
    db.session.commit()
    flash("Job visibility updated.", "success")
    return redirect(url_for("admin_jobs"))


@app.route("/admin/jobs/<int:job_id>/delete", methods=["POST"])
@role_required("admin")
def admin_delete_job(job_id):
    db.session.delete(db.get_or_404(Job, job_id))
    db.session.commit()
    flash("Job deleted.", "info")
    return redirect(url_for("admin_jobs"))


@app.route("/admin/taxonomy", methods=["GET", "POST"])
@role_required("admin")
def admin_taxonomy():
    if request.method == "POST":
        kind = request.form.get("kind")
        name = request.form.get("name", "").strip()
        model = Category if kind == "category" else Skill
        if not name:
            flash("Name is required.", "danger")
        elif model.query.filter(func.lower(model.name) == name.lower()).first():
            flash("That name already exists.", "warning")
        else:
            db.session.add(model(name=name))
            db.session.commit()
            flash(f"{kind.title()} added.", "success")
        return redirect(url_for("admin_taxonomy"))
    return render_template("admin_taxonomy.html",
                           categories=Category.query.order_by(Category.name).all(),
                           skills=Skill.query.order_by(Skill.name).all())


@app.route("/admin/taxonomy/<kind>/<int:item_id>/delete", methods=["POST"])
@role_required("admin")
def admin_taxonomy_delete(kind, item_id):
    if kind == "category":
        item = db.get_or_404(Category, item_id)
        if item.jobs:
            flash("Cannot delete a category that is used by jobs.", "danger")
            return redirect(url_for("admin_taxonomy"))
    elif kind == "skill":
        item = db.get_or_404(Skill, item_id)
    else:
        abort(404)
    db.session.delete(item)
    db.session.commit()
    flash("Deleted.", "info")
    return redirect(url_for("admin_taxonomy"))
