from flask import Flask
from flask_login import current_user   # <-- added for context processor
from app.config import Config
from app.extensions import db, login_manager, csrf
from app.models import Admin, Student, Notice   # <-- added Notice

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    # csrf.init_app(app)   # uncomment if you need CSRF protection

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.student import student_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # ----- Context processor for notification counts -----
    @app.context_processor
    def utility_processor():
        def get_notification_counts():
            counts = {'new_notices': 0, 'pending_students': 0}
            if current_user.is_authenticated:
                if isinstance(current_user, Student):
                    # Count notices newer than last viewed
                    if current_user.last_notice_viewed:
                        new_notices = Notice.query.filter(Notice.created_at > current_user.last_notice_viewed).count()
                    else:
                        new_notices = Notice.query.count()   # all notices are new if never viewed
                    counts['new_notices'] = new_notices
                elif isinstance(current_user, Admin):
                    counts['pending_students'] = Student.query.filter_by(status='pending').count()
            return counts
        return dict(notification_counts=get_notification_counts)
    # ----------------------------------------------------

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        # Try admin first
        admin = Admin.query.get(int(user_id))
        if admin:
            return admin
        # Then student
        return Student.query.get(int(user_id))

    return app