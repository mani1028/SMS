#!/usr/bin/env python
"""Test both super-admin login endpoints"""
import sys
sys.path.insert(0, '.')
from app import create_app

app = create_app()
client = app.test_client()

print('Testing both endpoints:')
print()

# Test old path (should 404)
print('1. Old path: /api/super-admin/login')
resp = client.post('/api/super-admin/login', json={'email': 'admin@platform.local', 'password': 'Admin@123456'})
print(f'   Status: {resp.status_code}')

# Test new path (should work)
print()
print('2. New path: /api/platform/super-admin/login')
resp = client.post('/api/platform/super-admin/login', json={'email': 'admin@platform.local', 'password': 'Admin@123456'})
print(f'   Status: {resp.status_code}')
if resp.status_code == 200:
    data = resp.get_json()
    print(f'   Message: {data.get("message")}')
    print('[SUCCESS] Correct endpoint is working!')
else:
    print(f'   Error: {resp.get_data(as_text=True)[:100]}')
