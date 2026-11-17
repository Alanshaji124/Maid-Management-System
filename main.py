import os
from flask import Flask, render_template
from admin import admin
from public import public
from customer import customer
from maid import maid_bp
import database  # Ensures database initialization

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "maid_booking_rajagiri_secure_key_2026")

# Register Blueprints
app.register_blueprint(public)
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(customer, url_prefix='/customer')
app.register_blueprint(maid_bp, url_prefix='/maid')

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return "<h3>Internal Server Error</h3><p>An unexpected error occurred. Please contact the administrator.</p>", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5437))
    print(f"[*] Starting Maid Booking Management System on http://localhost:{port}")
    app.run(debug=True, port=port)
