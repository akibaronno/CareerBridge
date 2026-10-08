from app import app
from app.seed import init_db

with app.app_context():
    init_db()

print("Database initialized successfully.")