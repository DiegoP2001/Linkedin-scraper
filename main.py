from app import app, db
from models.models import db
from flask_migrate import Migrate

if __name__ == '__main__':
    migrate = Migrate(app, db)
    with app.app_context():
        db.create_all()  # Crear las tablas en la base de datos si no existen
    app.run(host="0.0.0.0")
