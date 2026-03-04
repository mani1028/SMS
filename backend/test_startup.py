"""Quick test: can the app start?"""
from app import create_app

app = create_app()
rules = [r for r in app.url_map.iter_rules() if r.endpoint != 'static']
print(f"SUCCESS: App started with {len(rules)} routes")

# List blueprints
bps = sorted(app.blueprints.keys())
print(f"Blueprints ({len(bps)}): {', '.join(bps)}")
