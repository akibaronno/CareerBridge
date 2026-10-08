from datetime import datetime, date
from functools import wraps

from flask import abort
from flask_login import (login_required, current_user)
from sqlalchemy import func, or_

from app.extensions import db
from app.constants import ALLOWED_CV_EXT
from app.models import Job, Notification, Skill


def role_required(*roles):
    """Allow a route only for the given roles."""
    def decorator(fn):
        @wraps(fn)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def notify(user_id, message, link=None):
    db.session.add(Notification(user_id=user_id, message=message, link=link))


def allowed_cv(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_CV_EXT


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def to_int(value, default=0):
    try:
        return max(0, int(value))
    except (ValueError, TypeError):
        return default


def skills_from_form(form):
    """Read ticked skill checkboxes + comma separated new skills from a form."""
    ids = [int(i) for i in form.getlist("skills") if i.isdigit()]
    skills = Skill.query.filter(Skill.id.in_(ids)).all() if ids else []
    for name in (form.get("new_skills") or "").split(","):
        name = name.strip()
        if not name:
            continue
        skill = Skill.query.filter(func.lower(Skill.name) == name.lower()).first()
        if not skill:
            skill = Skill(name=name[:80])
            db.session.add(skill)
        if skill not in skills:
            skills.append(skill)
    return skills


def open_jobs_query():
    return Job.query.filter(Job.is_active.is_(True),
                            or_(Job.deadline.is_(None), Job.deadline >= date.today()))


def employer_owns(job):
    return (current_user.is_authenticated and current_user.role == "employer"
            and current_user.employer and current_user.employer.company
            and job.company_id == current_user.employer.company.id)


def current_seeker():
    if current_user.is_authenticated and current_user.role == "seeker":
        return current_user.jobseeker
    return None
