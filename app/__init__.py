from flask import Flask, render_template, flash
from flask_login import login_required, current_user

from .config import Config
from .extensions import db, login_manager
from .model import init_enum_tables
from .model.Tasks import Task

from .routes.auth.auth import auth_bp
from .routes.tasks.tasks import task_bp
from .routes.projects.projects import project_bp

from .services.ProjectService import ProjectService
from .services.TaskService import TaskService

def create_app():
    static_dir = 'static'
    template_dir = 'templates'

    app = Flask(__name__, static_folder=static_dir, template_folder=template_dir)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Log in required.'

    with app.app_context():
        db.create_all()
        init_enum_tables(db)
        
    app.register_blueprint(auth_bp, url_prefix='')
    app.register_blueprint(task_bp, url_prefix='/tasks')
    app.register_blueprint(project_bp, url_prefix='/projects')

    
    @app.route('/')
    def index():
        if not current_user.is_authenticated:
            return render_template('index.html')
        
        try:
            projects = ProjectService.get_participation_projects(current_user.id)
            tasks = TaskService.get_tasks_assigned_to_user(current_user.id)
            n = app.config['HOME_PAGE_DUE_TASKS_AMOUNT']
            tasks = TaskService.sort_tasks(tasks, 'due')[:n]
        except Exception as e:
            flash(f'Error occured in {__name__}: {e}')
            print(f'Error occured in {__name__}: {e}')
            return render_template('index.html')
        
        return render_template(
            'index.html',
            tasks=tasks,
            projects=projects
        )

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html')

        
    return app