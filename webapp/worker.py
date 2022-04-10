import sys
import time
from multiprocessing import Process

from flask import Blueprint
from flask import current_app as app

from webapp.managers import AppConfigManager, ExternalTaskManager
from webapp.repositories import AppDatabase, Status
from webapp.utils import get_exception_info


blueprint = Blueprint("worker", __name__)
config = AppConfigManager(lambda: app.config)


def check_solution(
    core_path: str,
    group_title: str,
    task: int,
    variant: int,
    code: str
):
    if core_path not in sys.path:
        sys.path.insert(1, core_path)
    from check_solution import check_solution
    (ok, error) = check_solution(
        group=group_title,
        task=task,
        variant=variant,
        code=code,
    )
    return (ok, error)


def load_tests(core_path: str):
    if core_path not in sys.path:
        sys.path.insert(1, core_path)
    from loaded_tests import GROUPS, TASKS
    return GROUPS, TASKS


def process_pending_messages(core_path: str, db: AppDatabase):
    pending_messages = db.messages.get_pending_messages_unique()
    message_count = len(pending_messages)
    if message_count == 0:
        return
    print(f"Processing {message_count} incoming messages...")
    for message in pending_messages:
        group = db.groups.get_by_id(message.group)
        task = db.tasks.get_by_id(message.task)
        variant = db.variants.get_by_id(message.variant)
        seed = db.seeds.get_final_seed(group.id)
        e = ExternalTaskManager(group, seed, db.tasks, db.groups, db.variants)
        ext = e.get_external_task(task.id, variant.id)
        print(f"g-{message.group}, t-{message.task}, v-{message.variant}")
        print(f"external: {ext.group_title}, t-{ext.task}, v-{ext.variant}")
        try:
            (ok, error) = check_solution(
                core_path=core_path,
                group_title=ext.group_title,
                task=ext.task,
                variant=ext.variant,
                code=message.code,
            )
            print(f"Check result: {ok}, {error}")
            status = Status.Checked if ok else Status.Failed
            db.messages.mark_as_processed(
                task=message.task,
                variant=message.variant,
                group=message.group,
            )
            db.statuses.update_status(
                task=message.task,
                variant=message.variant,
                group=message.group,
                status=status,
                output=error,
            )
        except BaseException:
            exception = get_exception_info()
            print(f"Error occured while checking for messages: {exception}")


def background_worker(connection_string: str, core_path: str):
    print(f"Starting background worker for database: {connection_string}")
    db = AppDatabase(lambda: connection_string)
    while True:
        try:
            process_pending_messages(core_path, db)
        except BaseException:
            exception = get_exception_info()
            print(f"Error occured inside the loop: {exception}")
        time.sleep(10)


@blueprint.before_app_first_request
def start_background_worker():
    if config.config.no_background_worker is True:
        return
    path = config.config.core_path
    connection = config.config.connection_string
    process = Process(target=background_worker, args=(connection, path))
    try:
        process.start()
        app.config["WORKER_PID"] = process.pid
    except BaseException:
        exception = get_exception_info()
        print(f"Error occured while starting process: {exception}")
