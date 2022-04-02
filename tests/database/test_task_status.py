from tests.utils import unique_int, unique_str

from webapp.models import TaskStatusEnum
from webapp.repositories import AppDatabase


def test_task_status_creation(db: AppDatabase):
    task = unique_int()
    variant = unique_int()
    group = unique_int()
    code = unique_str()

    db.statuses.submit_task(task, variant, group, code)
    task_statuses = db.statuses.get_all()

    assert any(task_status.task == task for task_status in task_statuses)


def test_task_status_fetching_by_group(db: AppDatabase):
    task_1 = unique_int()
    task_2 = unique_int()
    variant = unique_int()
    group = unique_int()
    code = unique_str()

    db.statuses.submit_task(task_1, variant, group, code)
    db.statuses.submit_task(task_2, variant, group, code)

    task_status = db.statuses.get_by_group(group)
    assert all([task.task == task_1 or task.task == task_2 for task in task_status])


def test_task_status_get_task_status(db: AppDatabase):
    task = unique_int()
    variant = unique_int()
    group = unique_int()
    code = unique_str()
    db.statuses.submit_task(task, variant, group, code)

    task_status = db.statuses.get_task_status(task, variant, group)
    assert task_status.task == task
    assert task_status.variant == variant
    assert task_status.group == group
    assert task_status.code == code
    assert task_status.status == TaskStatusEnum.Submitted


def test_task_status_update_status(db: AppDatabase):
    variant = unique_int()
    group = unique_int()
    code = unique_str()
    task = unique_int()
    output = unique_str()

    db.statuses.submit_task(task, variant, group, code)

    for ts_enum in TaskStatusEnum:
        if ts_enum != TaskStatusEnum.Checked:
            db.statuses.update_status(task, variant, group, ts_enum.value, output)
            task_status = db.statuses.get_task_status(task, variant, group)
            assert task_status.status == ts_enum.value

    db.statuses.update_status(task, variant, group, TaskStatusEnum.Checked, output)
    task_status = db.statuses.get_task_status(task, variant, group)
    assert task_status.status == TaskStatusEnum.Checked
