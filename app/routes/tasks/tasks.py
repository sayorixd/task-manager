import datetime
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user

from ...services.TaskService import TaskService
from ...services.TeamService import TeamService

task_bp = Blueprint('task', __name__, static_folder='../../static', template_folder='../../templates')


@task_bp.route('/')
@login_required
def tasks():
    sort = request.args.get('sort', 'id')
    order = request.args.get('order', 'asc')
    try:
        tasks = TaskService.get_tasks_assigned_to_user(current_user.id)
        sorted_tasks = TaskService.sort_tasks(tasks, sort, order)
    except ValueError as e:
        print(f'ValueError in {__name__}: {e}')
        flash('Server error.', category='error')
        tasks = []

    datetime_now = datetime.datetime.now()
    upcoming_tasks = []
    overdue_tasks = []
    for task in tasks:
        if datetime_now <= task.deadline:
            upcoming_tasks.append(task)
        else:
            overdue_tasks.append(task)

    return render_template(
        'tasks.html', 
        upcoming_tasks=upcoming_tasks,
        overdue_tasks=overdue_tasks,
        sort=sort,
        order=order,
        sorts=TaskService.get_available_sorts()
    )


@task_bp.route('/<int:id>', methods=['GET', 'POST'])
def task(id):
    try:
        task = TaskService.get_task(id)
        proj_id = task.projectID
        assignedTo = task.assignedTo
    except ValueError:
        flash('Task not found', category='error')
        return redirect(url_for('task.tasks'))
    except Exception as e:
        print(f'Error occured in {__name__}: {e}')
        flash('Server error.', category='error')
        return redirect(url_for('task.tasks'))

    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('Log in to edit tasks.', category='error')
            return redirect(url_for('auth.login'))

        try:
            data = TaskService.build_update_data(request.form)
            task = TaskService.update_task(id, data)
            flash('Task updated.', category='success')
            return redirect(url_for('project.project', id=proj_id))
        except ValueError as e:
            flash(str(e), category='error')
            return redirect(url_for('project.project', id=proj_id))

    members = TeamService.get_project_members(proj_id)

    return render_template(
        'task.html',
        task=task,
        members=members,
        statuses=TaskService.get_all_statuses(),
        priorities=TaskService.get_all_priorities(),
    )
