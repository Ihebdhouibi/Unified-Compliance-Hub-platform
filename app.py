from flask import Flask, render_template


def create_app():
    app = Flask(__name__, static_folder="static")

    # Import routes after creating the app to avoid circular imports
    from routes import auth_bp, dashboard_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")

    @app.route("/")
    def index():
        return render_template("index.html")

    return app
