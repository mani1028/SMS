#!/usr/bin/env python
from flask_migrate import stamp
from app import create_app

app = create_app()
with app.app_context():
    stamp(revision='saas_billing_001')
    print("✓ Migration stamped to saas_billing_001")
