# run.py

from app import create_app, db
from sqlalchemy import inspect

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("[DEBUG] Tables:", inspect(db.engine).get_table_names())

    app.run(host="0.0.0.0", port=5000)
