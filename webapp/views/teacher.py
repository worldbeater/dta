from flask_jwt_extended import create_access_token, set_access_cookies, unset_jwt_cookies, verify_jwt_in_request
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError

from flask import Blueprint
from flask import current_app as app
from flask import make_response, redirect, render_template, request

from webapp.forms import TeacherLoginForm
from webapp.managers import AppConfigManager, ExportManager, StatusManager, TeacherManager
from webapp.models import Message, Status, Teacher
from webapp.repositories import AppDatabase
from webapp.utils import get_exception_info, teacher_jwt_required


blueprint = Blueprint("teacher", __name__)
config = AppConfigManager(lambda: app.config)
db = AppDatabase(lambda: config.config.connection_string)

statuses = StatusManager(db.tasks, db.groups, db.variants, db.statuses, config, db.seeds)
exports = ExportManager(db.groups, db.messages, statuses, db.variants, db.tasks)
teachers = TeacherManager(db.teachers)


@blueprint.route("/teacher", methods=["GET"])
@teacher_jwt_required(db.teachers)
def dashboard(teacher: Teacher):
    groups = db.groups.get_all() if config.config.no_background_worker else None
    return render_template("teacher/dashboard.jinja", groups=groups)


@blueprint.route("/teacher/group/select", methods=["GET"])
@teacher_jwt_required(db.teachers)
def select_group(teacher: Teacher):
    group = request.args.get('group')
    if config.config.exam:
        return redirect(f'/teacher/group/{group}/exam')
    return redirect(f'/teacher/group/{group}')


@blueprint.route("/teacher/group/<group_id>/exam", methods=["GET"])
@teacher_jwt_required(db.teachers)
def exam(teacher: Teacher, group_id: int):
    group = db.groups.get_by_id(group_id)
    seed = db.seeds.get_final_seed(group_id)
    return render_template("teacher/exam.jinja", group=group, seed=seed)


@blueprint.route("/teacher/group/<group_id>/exam/toggle", methods=["GET"])
@teacher_jwt_required(db.teachers)
def exam_toggle(teacher: Teacher, group_id: int):
    seed = db.seeds.get_final_seed(group_id)
    if seed is None and config.config.final_tasks:
        db.seeds.begin_final_test(group_id)
    elif seed is not None and seed.active:
        db.seeds.end_final_test(group_id)
    elif seed is not None:
        db.seeds.continue_final_test(group_id)
    return redirect(f'/teacher/group/{group_id}/exam')


@blueprint.route("/teacher/group/<group_id>/exam/csv", methods=["GET"])
@teacher_jwt_required(db.teachers)
def exam_csv(teacher: Teacher, group_id: int):
    delimiter = request.args.get('delimiter')
    value = exports.export_exam_results(group_id, delimiter)
    output = make_response(value)
    output.headers["Content-Disposition"] = f"attachment; filename={group_id}.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@blueprint.route("/teacher/messages", methods=["GET"])
@teacher_jwt_required(db.teachers)
def messages(teacher: Teacher):
    separator = request.args.get('separator')
    count = request.args.get('count')
    value = exports.export_messages(count, separator)
    output = make_response(value)
    output.headers["Content-Disposition"] = "attachment; filename=messages.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@blueprint.route("/teacher/group/<group_id>", methods=["GET"])
@teacher_jwt_required(db.teachers)
def queue(teacher: Teacher, group_id: int):
    group = db.groups.get_by_id(group_id)
    message = db.messages.get_next_pending_message()
    matches = message is None or group.id == message.group
    if matches and config.config.no_background_worker:
        return render_template("teacher/queue.jinja", group=group, message=message)
    return redirect(f'/teacher')


@blueprint.route("/teacher/group/<group_id>/queue/<message_id>/accept", methods=["GET"])
@teacher_jwt_required(db.teachers)
def accept(teacher: Teacher, group_id: int, message_id: int):
    group = db.groups.get_by_id(group_id)
    message = db.messages.get_by_id(message_id)
    if group.id == message.group and config.config.no_background_worker:
        process_message(message, Status.Checked, None)
    return redirect(f"/teacher/group/{group_id}")


@blueprint.route("/teacher/group/<group_id>/queue/<message_id>/reject", methods=["GET"])
@teacher_jwt_required(db.teachers)
def reject(teacher: Teacher, group_id: int, message_id: int):
    group = db.groups.get_by_id(group_id)
    message = db.messages.get_by_id(message_id)
    if group.id == message.group and config.config.no_background_worker:
        comment = request.args.get("comment")
        process_message(message, Status.Failed, comment)
    return redirect(f"/teacher/group/{group_id}")


@blueprint.route("/teacher/login", methods=['GET', 'POST'])
def login():
    if verify_jwt_in_request(True):
        response = redirect('/teacher/login')
        unset_jwt_cookies(response)
        return response
    form = TeacherLoginForm()
    if not form.validate_on_submit():
        return render_template("teacher/login.jinja", form=form)
    teacher = teachers.check_password(form.login.data, form.password.data)
    if teacher is None:
        return render_template("teacher/login.jinja", form=form)
    access = create_access_token(identity=teacher.id, additional_claims={"teacher": True})
    response = redirect("/teacher")
    set_access_cookies(response, access)
    return response


@blueprint.route("/teacher/logout", methods=['GET'])
def logout():
    response = redirect("/teacher/login")
    unset_jwt_cookies(response)
    return response


@blueprint.errorhandler(Exception)
def handle_view_errors(e):
    print(get_exception_info())
    return render_template("error.jinja", redirect="/teacher")


@blueprint.errorhandler(JWTExtendedException)
@blueprint.errorhandler(PyJWTError)
def handle_authorization_errors(e):
    response = redirect('/teacher/login')
    unset_jwt_cookies(response)
    return response


def process_message(message: Message, status: Status, comment: str | None):
    db.messages.mark_as_processed(message.id)
    db.statuses.update_status(
        task=message.task,
        variant=message.variant,
        group=message.group,
        code=message.code,
        status=status,
        ip=message.ip,
        output=comment,
    )
    db.checks.record_check(
        message=message.id,
        status=status,
        output=comment,
    )
