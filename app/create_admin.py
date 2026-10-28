import sys
from pathlib import Path
import os

# Add 'app' directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import SessionLocal, engine
from passlib.context import CryptContext
import models

# Ensure tables exist
models.Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Read credentials from command-line arguments, environment, or default fallback
if len(sys.argv) >= 3:
    username = sys.argv[1].strip()
    password = sys.argv[2].strip()
else:
    username = os.getenv("ADMIN_USERNAME", "admin").strip()
    password = os.getenv("ADMIN_PASSWORD", "admin123").strip()

db = SessionLocal()

try:
    existing_admin = db.query(models.AdminUser).filter(models.AdminUser.username == username).first()

    if existing_admin:
        existing_admin.password = pwd_context.hash(password)
        print(f"[OK] Admin user '{username}' password updated successfully.")
    else:
        admin = models.AdminUser(
            username=username,
            password=pwd_context.hash(password)
        )
        db.add(admin)
        print(f"[OK] Admin user '{username}' created successfully.")

    db.commit()
except Exception as e:
    db.rollback()
    print(f"[ERROR] Failed to create or update admin user: {e}")
    sys.exit(1)
finally:
    db.close()
