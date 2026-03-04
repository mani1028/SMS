import os
from app import create_app
from app.config import DevelopmentConfig, ProductionConfig

# Determine environment
env = os.getenv('FLASK_ENV', 'development')
config_class = DevelopmentConfig if env == 'development' else ProductionConfig

# Create app
app = create_app(config_class)

# Start background scheduler for subscription automation
try:
    from background_jobs.scheduler import start_scheduler
    start_scheduler()
except Exception as e:
    print(f"[Scheduler] Could not start background scheduler: {e}")

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
