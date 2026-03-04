#!/usr/bin/env python
from flask_migrate import upgrade
from app import create_app, db

app = create_app()
with app.app_context():
    upgrade()
    print("✓ Database migration completed successfully")
