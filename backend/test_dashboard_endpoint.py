#!/usr/bin/env python
"""Test the analytics dashboard endpoint directly"""
import sys
sys.path.insert(0, '.')

from app import create_app
from app.core.auth import token_required
from app.core.response import success_response
import json

app = create_app()

# Create test JWT token for superadmin
from flask_jwt_extended import create_access_token
with app.app_context():
    admin_token = create_access_token(identity=str(1))  # User ID 1 is superadmin
    print(f"[OK] Generated test token: {admin_token[:20]}...")
    
    # Test the dashboard endpoint by calling it directly
    from flask import Flask
    from flask.testing import FlaskClient
    
    client = app.test_client()
    
    # Test without token (should get 401)
    print("\n1. Testing without token:")
    resp = client.get('/api/analytics/dashboard')
    print(f"   Status: {resp.status_code}")
    data = resp.get_json()
    if data:
        print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
    
    # Test with token
    print("\n2. Testing with valid token:")
    resp = client.get('/api/analytics/dashboard', headers={
        'Authorization': f'Bearer {admin_token}'
    })
    print(f"   Status: {resp.status_code}")
    data = resp.get_json()
    if data:
        print(f"   Response keys: {list(data.keys())}")
        if 'data' in data:
            print(f"   Data keys: {list(data.get('data', {}).keys())}")
            dashboard_data = data['data']
            print(f"\n   Schools: {dashboard_data.get('schools', {})}")
            print(f"   Revenue: {dashboard_data.get('revenue', {})}")
            print(f"   Users: {dashboard_data.get('users', {})}")
            print(f"   Payments: {dashboard_data.get('payments', {})}")
            print(f"   Subscriptions: {dashboard_data.get('subscriptions', {})}")
        if resp.status_code == 200:
            print("\n[SUCCESS] Dashboard endpoint working!")
        else:
            print(f"\n[ERROR] Got status {resp.status_code}")
    else:
        print(f"   [ERROR] No JSON response: {resp.get_data(as_text=True)}")
