from datetime import datetime

from flask import Config

from webapp.models import FinalSeed, Group, Status, Student, Task, TaskBlock, TaskStatus, TypeOfTask, Variant


class AppConfig:
    def __init__(self, config: Config):
        self.highlight_syntax: bool = config["HIGHLIGHT_SYNTAX"]
        self.core_path: str = config["CORE_PATH"]
        self.analytics_path: str = config["ANALYTICS_PATH"]
        self.api_token: str = config["API_TOKEN"]
        self.connection_string: str = config["CONNECTION_STRING"]
        self.task_base_path: str = config["TASK_BASE_PATH"]
        self.no_background_worker: bool = config["DISABLE_BACKGROUND_WORKER"]
        self.final_tasks: dict[str, list[int]] = config["FINAL_TASKS"]
        self.final_variants: int = config["FINAL_VARIANTS"]
        self.clearable_database: bool = config["CLEARABLE_DATABASE"]
        self.readonly: bool = config["READONLY"]
        self.enable_registration: bool = config["ENABLE_REGISTRATION"]
        self.imap_login: bool = config["IMAP_LOGIN"]
        self.imap_password: bool = config["IMAP_PASSWORD"]
        self.enable_lks_oauth: bool = config["ENABLE_LKS_OAUTH"]
        self.lks_oauth_client_id: str = config["LKS_OAUTH_CLIENT_ID"]
        self.lks_oauth_client_secret: str = config["LKS_OAUTH_CLIENT_SECRET"]
        self.lks_api_base_url: str = config["LKS_API_BASE_URL"]
        self.lks_redirect_url: str = config["LKS_REDIRECT_URL"]
        self.places_in_rating: int = config["PLACES_IN_RATING"]
        self.places_in_group: int = config["PLACES_IN_GROUP"]
        self.groups: dict = config["GROUPS"]
        self.enable_manual_password_change: bool = config["ENABLE_MANUAL_PASSWORD_CHANGE"]

    @property
    def registration(self) -> bool:
        return self.enable_registration


class ExternalTaskDto:
    def __init__(self, group: int, group_title: str, task: int, variant: int, active: bool):
        self.group_title = group_title
        self.group = group
        self.task = task
        self.variant = variant
        self.active = active


class TaskDto:
    def __init__(self, task: Task, block: TaskBlock | None, seed: FinalSeed | None):
        self.id = int(task.id)
        self.formulation = task.formulation
        self.active = task.type == TypeOfTask.Static or seed and seed.active
        self.is_random = task.type == TypeOfTask.Random
        self.block_title = block.title if block else ''
        self.block = block and block.id
        self.deadline = block.deadline if block else None


class AchievementDto:
    def __init__(self, order: int, active: bool, count: int):
        self.order = order
        self.active = active
        self.count = count

    @property
    def title(self):
        pop = 'Самое популярное' if self.order == 0 else f'{self.order + 1}-е по популярности'
        return f'{pop} решение'

    @property
    def description(self):
        endone = int(str(self.count)[-1]) == 1
        students = 'студентом' if endone else 'студентами'
        similarity = f'Похожим способом данная задача была решена {self.count} {students}.'
        return similarity


class TaskStatusDto:
    def __init__(
        self,
        group: Group,
        variant: Variant,
        task: TaskDto,
        status: TaskStatus | None,
        external: ExternalTaskDto,
        config: AppConfig,
        achievements: list[int],
        reviewer: Student | None,
    ):
        self.task = task.id
        self.deadline = task.deadline
        self.reviewer = reviewer.email if reviewer else None
        self.reviewed_at = status.reviewed_at or '' if status else ''
        self.earned = sum(1 for a in range(len(achievements)) if status and a in status.achievements)
        self.formulation = task.formulation
        self.ip = status.ip if status is not None else "-"
        self.variant = variant.id
        self.group = int(group.id)
        self.group_title = group.title
        self.external = external
        self.status = Status.NotSubmitted if status is None else status.status
        self.checked = self.status in [Status.Checked, Status.CheckedSubmitted, Status.CheckedFailed]
        self.readonly = config.readonly
        self.achievements = self.map_achievements(status, achievements)
        self.error_message = status.output if self.status in [
            Status.Failed,
            Status.CheckedFailed,
            Status.VerifiedFailed,
        ] else None

    @property
    def submission_url(self) -> str:
        gid = self.group
        vid = self.variant
        tid = self.task
        return f'/group/{gid}/variant/{vid}/task/{tid}'

    @property
    def formulation_url(self) -> str:
        gid = self.group
        vid = self.variant
        tid = self.task
        evid = self.external.variant
        return f'/files/task/{tid}/group/{gid}/variant/{vid}#вариант-{evid + 1}'

    @property
    def cell_background(self) -> str:
        return self.map_status({
            Status.Submitted: "inherit",
            Status.Checked: "#fff9e3",
            Status.CheckedSubmitted: "#fff9e3",
            Status.CheckedFailed: "#fff9e3",
            Status.Verified: "#e3ffee",
            Status.VerifiedSubmitted: "#e3ffee",
            Status.VerifiedFailed: "#e3ffee",
            Status.Failed: "#ffe3ee",
            Status.NotSubmitted: "inherit",
        })

    @property
    def name(self) -> str:
        return self.map_status({
            Status.Submitted: "Отправлено",
            Status.Checked: "Зачтено",
            Status.CheckedSubmitted: "Зачтено. Отправлено повторно",
            Status.CheckedFailed: "Зачтено. Ошибка при повторной отправке!",
            Status.Verified: "Защищено",
            Status.VerifiedSubmitted: "Защищено. Отправлено повторно",
            Status.VerifiedFailed: "Защищено. Ошибка при повторной отправке!",
            Status.Failed: "Ошибка!",
            Status.NotSubmitted: "Не отправлено",
        })

    @property
    def code(self) -> str:
        return self.map_status({
            Status.Submitted: "?",
            Status.Checked: "+",
            Status.CheckedSubmitted: "+",
            Status.CheckedFailed: "+",
            Status.Verified: "✓",
            Status.VerifiedSubmitted: "✓",
            Status.VerifiedFailed: "✓",
            Status.Failed: "x",
            Status.NotSubmitted: "x" if self.disabled else "-",
        })

    @property
    def color(self) -> str:
        return self.map_status({
            Status.Submitted: "secondary",
            Status.Checked: "warning",
            Status.CheckedSubmitted: "warning",
            Status.CheckedFailed: "warning",
            Status.Verified: "success",
            Status.VerifiedSubmitted: "success",
            Status.VerifiedFailed: "success",
            Status.Failed: "danger",
            Status.NotSubmitted: "secondary",
        })

    @property
    def show_achievements(self) -> bool:
        return self.achievements and self.status in [
            Status.Checked,
            Status.CheckedSubmitted,
            Status.CheckedFailed,
            Status.Verified,
            Status.VerifiedSubmitted,
            Status.VerifiedFailed,
        ]

    @property
    def can_verify(self) -> bool:
        return self.status in [
            Status.Checked,
            Status.CheckedSubmitted,
            Status.CheckedFailed,
        ]

    @property
    def can_unverify(self) -> bool:
        return self.status in [
            Status.Verified,
            Status.VerifiedSubmitted,
            Status.VerifiedFailed,
        ]

    @property
    def disabled(self) -> bool:
        lasting = not self.deadline or self.deadline > datetime.now()
        return not self.external.active or self.readonly or not lasting

    def map_achievements(self, status: TaskStatus | None, achievements: list[int]):
        dtos = []
        for order, count in enumerate(achievements):
            earned = status.achievements if status and status.achievements else []
            dto = AchievementDto(order, order in earned, count)
            dtos.append(dto)
        return dtos

    def map_status(self, map: dict[Status, str]):
        return map[self.status]


class VariantDto:
    def __init__(self, variant: Variant, statuses: list[TaskStatusDto], student: Student | None):
        self.id = int(variant.id)
        self.email = student.email if student else ''
        self.statuses = statuses
        self.earned = sum(s.earned for s in statuses)
        self.solved = sum(s.status in [
            Status.Verified,
            Status.VerifiedSubmitted,
            Status.VerifiedFailed,
        ] for s in statuses)


class GroupDto:
    def __init__(self, group: Group, tasks: list[TaskDto], variants: list[VariantDto]):
        self.title = str(group.title)
        self.id = int(group.id)
        self.tasks = tasks
        self.variants = variants


class StudentInRatingDto:
    def __init__(
        self,
        group: Group,
        variant: int,
        earned: int = 0
    ):
        self.group = group
        self.variant = variant
        self.earned = earned


class SubmissionDto:
    def __init__(
        self,
        status: TaskStatusDto,
        code: str,
        checked: str,
        sent: str,
        ip: str,
        student: Student | None
    ):
        self.status = status
        self.code = code
        self.checked = checked
        self.sent = sent
        self.student = student
        self.ip = ip


class GroupInRatingDto:
    def __init__(
        self,
        group: Group,
        earned: int = 0
    ):
        self.group = group
        self.earned = earned
