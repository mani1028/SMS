import os
from app import create_app
from app.config import DevelopmentConfig, ProductionConfig

# Determine environment
env = os.getenv('FLASK_ENV', 'development')
config_class = DevelopmentConfig if env == 'development' else ProductionConfig

# Create app
app = create_app(config_class)

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)
