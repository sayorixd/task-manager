from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from ...services.ProjectService import ProjectService
from ...services.TeamService import TeamService
from ...services.TaskService import TaskService
from ...services.UserService import UserService

project_bp = Blueprint('project', __name__, static_folder='../../static', template_folder='../../templates')


@project_bp.route('/')
@login_required
def projects():
    user_projects = []
    participating_projects = []
    try:
        user_projects = ProjectService.get_user_projects(current_user.id)
        participating_projects = ProjectService.get_participation_projects(current_user.id)
    except ValueError as e:
        print(f'ValueError in {__name__}: {e}')
        flash('Server error.', category='error')

    return render_template(
        'projects.html',
        user_projects=user_projects,
        participating_projects=participating_projects
    )


@project_bp.route('/<int:id>')
@login_required
def project(id):
    sort = request.args.get('sort', 'id')
    order = request.args.get('order', 'asc')
    try:
        project = ProjectService.get_project(id)
        tasks = ProjectService.get_sorted_tasks(id, sort, order)
        teams = TeamService.get_project_teams(id)
    except ValueError as e:
        print(f'ValueError in {__name__}: {e}')
        flash(str(e), category='error')
        return redirect(url_for('project.projects'))

    team_members = TeamService.get_project_members(project.id)

    return render_template(
        'project.html',
        project=project,
        tasks=tasks,
        teams=teams,
        team_members=team_members,
        sort=sort,
        order=order,
        sorts=ProjectService.get_available_sorts(),
    )

@project_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        try:
            project = ProjectService.create_project({
                'name': request.form.get('name'),
                'description': request.form.get('description'),
                'createdBy': current_user.id,
                'status': request.form.get('status')
            })
            flash('Project created.', category='success')
            return redirect(url_for('project.project', id=project.id))
        except ValueError as e:
            flash(str(e), category='error')
            return redirect(url_for('project.new'))

    return render_template(
        'project-form.html',
        statuses=ProjectService.get_all_statuses(),
        task=None,
    )

@project_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if request.method == 'POST':
        try:
            project = ProjectService.update_project(
                request.form.get('id'),
                {
                    'name': request.form.get('name'),
                    'description': request.form.get('description'),
                    'createdBy': current_user.id,
                    'status': request.form.get('status')
                }
            )
            flash('Successful edit.', category='success')
            return redirect(url_for('project.project', id=project.id))
        except ValueError as e:
            flash(str(e), category='error')
            return redirect(url_for('project.new'))

    try:
        project = ProjectService.get_project(id)
    except ValueError as e:
        print(f'ValueError in {__name__}: {e}')
        flash(str(e), category='error')
        return redirect(url_for('project.projects'))

    return render_template(
        'project-form.html',
        statuses=ProjectService.get_all_statuses(),
        project=project
    )

@project_bp.route('/<int:id>/team/create', methods=['GET', 'POST'])
@login_required
def new_team(id):
    try:
        project = ProjectService.get_project(id)
    except ValueError as e:
        flash(str(e), category='error')
        return redirect(url_for('project.projects'))

    if request.method == 'POST':
        try:
            team = TeamService.create_team(
                {
                    'projectID': project.id,
                    'name': request.form.get('name')
                }
            )
            flash('Team successfully created.', category='success')
            return redirect(url_for('project.project', id=id))
        except ValueError as e:
            flash(str(e), category='error')
            return redirect(url_for('project.project', id=id))

    return render_template(
        'team-form.html',
        project_id=project.id
    )

@project_bp.route('/<int:id>/team/add_member', methods=['GET', 'POST'])
@login_required
def add_member(id):
    try:
        project = ProjectService.get_project(id)
    except ValueError as e:
        flash(str(e), category='error')
        return redirect(url_for('project.projects'))

    team = None
    try:
        team = TeamService.get_project_teams(project.id)[0]
    except:
        flash('Team does not exist for this team.', category='error')
        return redirect(url_for('project.project', id=id))

    if request.method == 'POST':
        try:
            TeamService.add_member_to_team({
                'id': team.id,
                'user_id': request.form.get('user_id')
            })
            flash('Member successfully added', category='success')
            return redirect(url_for('project.project', id=project.id))
        except ValueError as e:
            flash(str(e), category='error')
            return redirect(url_for('project.project', id=project.id))

    users = UserService.get_all_users()

    return render_template(
        'team-add-member-form.html',
        team=team,
        users=users,
        project_id=project.id
    )

@project_bp.route('/<int:id>/tasks/new', methods=['GET', 'POST'])
@login_required
def new_task(id):
    try:
        project = ProjectService.get_project(id)
    except ValueError as e:
        flash(str(e), category='error')
        return redirect(url_for('project.projects'))

    if request.method == 'POST':
        try:
            assigned_to = request.form.get('assignedTo')
            TaskService.create_task({
                'name': request.form.get('name'),
                'description': request.form.get('description'),
                'createdBy': current_user.id,
                'projectID': project.id,
                'status': request.form.get('status'),
                'priority': request.form.get('priority'),
                'deadline': TaskService.parse_deadline(request.form.get('deadline')),
                'assignedTo': assigned_to if assigned_to != '' else None
            })
            flash('Task created.', category='success')
            return redirect(url_for('project.project', id=project.id))
        except ValueError as e:
            flash(str(e), category='error')

    members = TeamService.get_project_members(id)

    return render_template(
        'task_form.html',
        project=project,
        members=members,
        statuses=TaskService.get_all_statuses(),
        priorities=TaskService.get_all_priorities(),
        task=None,
    )
