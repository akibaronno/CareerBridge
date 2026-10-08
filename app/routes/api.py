"""REST API (JSON)."""

from flask import (request, url_for, jsonify)
from flask_login import (login_required, current_user)

from app import app
from app.extensions import db
from app.models import Job, Notification
from app.helpers import current_seeker, open_jobs_query, role_required
from app.matching import calculate_match, recommended_jobs


def job_to_dict(job, match=None):
    data = {"id": job.id, "title": job.title, "company": job.company.name,
            "category": job.category.name if job.category else None,
            "location": job.location, "job_type": job.job_type, "salary": job.salary,
            "experience_required": job.experience_required,
            "deadline": job.deadline.isoformat() if job.deadline else None,
            "skills": [s.name for s in job.skills], "description": job.description,
            "url": url_for("job_detail", job_id=job.id)}
    if match:
        data["match"] = match
    return data


@app.route("/api/jobs")
def api_jobs():
    query = open_jobs_query()
    if request.args.get("q"):
        query = query.filter(Job.title.ilike(f"%{request.args['q']}%"))
    if request.args.get("category", type=int):
        query = query.filter(Job.category_id == request.args.get("category", type=int))
    if request.args.get("location"):
        query = query.filter(Job.location.ilike(f"%{request.args['location']}%"))
    if request.args.get("job_type"):
        query = query.filter(Job.job_type == request.args["job_type"])
    return jsonify([job_to_dict(j) for j in query.order_by(Job.created_at.desc()).all()])


@app.route("/api/jobs/<int:job_id>")
def api_job(job_id):
    job = db.get_or_404(Job, job_id)
    seeker = current_seeker()
    return jsonify(job_to_dict(job, calculate_match(job, seeker) if seeker else None))


@app.route("/api/match/<int:job_id>")
@role_required("seeker")
def api_match(job_id):
    job = db.get_or_404(Job, job_id)
    return jsonify(calculate_match(job, current_user.jobseeker))


@app.route("/api/recommendations")
@role_required("seeker")
def api_recommendations():
    return jsonify([job_to_dict(j, m) for j, m in recommended_jobs(current_user.jobseeker, 20)])


@app.route("/api/notifications")
@login_required
def api_notifications():
    items = current_user.notifications.order_by(Notification.created_at.desc()).limit(50).all()
    return jsonify([{"id": n.id, "message": n.message, "is_read": n.is_read,
                     "created_at": n.created_at.isoformat()} for n in items])
