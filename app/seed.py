"""Database creation + seed data (categories, skills, admin account)."""

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app import app
from app.extensions import db
from app.models import Category, Skill, User


DEFAULT_CATEGORIES = ["Software Development", "Data & Analytics", "Design & Creative", "Marketing & Sales",
                      "Finance & Accounting", "Human Resources", "Customer Support", "Engineering",
                      "Education", "Healthcare"]
DEFAULT_SKILLS = ["Python", "Flask", "Django", "JavaScript", "HTML", "CSS", "Bootstrap", "React", "Node.js",
                  "SQL", "MySQL", "PostgreSQL", "MongoDB", "Git", "Docker", "Linux", "Java", "C++", "C#",
                  "REST API", "Machine Learning", "Data Analysis", "Excel", "Power BI", "Figma", "UI/UX Design",
                  "Communication", "Project Management", "Digital Marketing", "SEO", "Accounting"]


def ensure_database():
    """Create the MySQL database if it does not exist yet."""
    url = make_url(app.config["SQLALCHEMY_DATABASE_URI"])
    if url.get_backend_name() != "mysql":
        return
    engine = create_engine(url.set(database=None))
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{url.database}` CHARACTER SET utf8mb4"))
        conn.commit()
    engine.dispose()


def init_db():
    ensure_database()
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(role="admin").first():
            admin = User(name="Administrator", email="admin@portal.com", role="admin")
            admin.set_password("Admin@123")
            db.session.add(admin)
        if Category.query.count() == 0:
            db.session.add_all([Category(name=n) for n in DEFAULT_CATEGORIES])
        if Skill.query.count() == 0:
            db.session.add_all([Skill(name=n) for n in DEFAULT_SKILLS])
        db.session.commit()


@app.cli.command("init-db")
def init_db_command():
    """flask --app app init-db"""
    init_db()
    print("Database ready. Admin: admin@portal.com / Admin@123")


