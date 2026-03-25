from flask import Flask, send_from_directory, abort
from utils.db import init_db
from routes.auth_routes import auth_bp
from routes.contributor_routes import contributor_bp
from routes.reviewer_routes import reviewer_bp
from routes.admin_routes import admin_bp
from utils.helpers import format_datetime_ist
import os

app = Flask(__name__)
app.secret_key = "secret"

# Add template filter for IST time formatting
app.jinja_env.filters['ist_time'] = format_datetime_ist

UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), "uploads")

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    fullpath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(fullpath) and os.path.isfile(fullpath):
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    abort(404)

app.register_blueprint(auth_bp)
app.register_blueprint(contributor_bp)
app.register_blueprint(reviewer_bp)
app.register_blueprint(admin_bp)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)