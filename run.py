"""Start the project:  python run.py"""
from app import app
from app.seed import init_db

if __name__ == "__main__":
    init_db()
    print("Admin login -> admin@portal.com / Admin@123")
    app.run(debug=True)
