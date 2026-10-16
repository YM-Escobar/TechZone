from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError
from app.Models.community import Comment, Report, ReportStatus
from app.Models.user import User, UserRole
from app.Repository.advisory_repository import AdvisoryRepository
from app.Repository.build_repository import BuildRepository
from app.Repository.community_repository import CommentRepository, PostRepository, ReportRepository
from app.Repository.product_repository import ProductRepository
from app.Repository.user_repository import UserRepository
from app.Schema.common_schema import PageResult, update_data
from app.Schema.user_schema import AdminStats, AdminUserCreate, AdminUserUpdate, UserStats
from app.Services import storage
from app.Services.auth import create_user, ensure_user_unique
from app.Services.profile import PROFILE_NULLABLE


class AdminService:
    def __init__(self, db: Session):
        self.users = UserRepository(db)
        self.products = ProductRepository(db)
        self.builds = BuildRepository(db)
        self.posts = PostRepository(db)
        self.comments = CommentRepository(db)
        self.advisories = AdvisoryRepository(db)
        self.reports = ReportRepository(db)

    def list_users(
        self,
        skip: int,
        limit: int,
        search: str | None = None,
        role: UserRole | None = None,
        is_active: bool | None = None,
    ) -> PageResult[User]:
        items, total = self.users.list(skip, limit, search=search, role=role, is_active=is_active)
        return PageResult(items, total, skip, limit)

    def get_user(self, user_id: int) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("Usuario no encontrado")
        return user

    def create_user(self, data: AdminUserCreate) -> User:
        # Las cuentas creadas por un admin se consideran verificadas
        return create_user(self.users, data, role=data.role, is_verified=True)

    def update_user(self, user_id: int, data: AdminUserUpdate) -> User:
        user = self.get_user(user_id)
        changes = update_data(data, PROFILE_NULLABLE)
        if "email" in changes:
            changes["email"] = changes["email"].lower()
        ensure_user_unique(
            self.users, email=changes.get("email"), username=changes.get("username"), exclude_id=user.id
        )
        for field, value in changes.items():
            setattr(user, field, value)
        return self.users.save(user)

    def change_role(self, actor: User, user_id: int, role: UserRole) -> User:
        user = self._get_other_user(actor, user_id, "No puedes cambiar tu propio rol")
        user.role = role
        return self.users.save(user)

    def set_status(self, actor: User, user_id: int, is_active: bool) -> User:
        user = self._get_other_user(actor, user_id, "No puedes desactivar tu propia cuenta")
        user.is_active = is_active
        return self.users.save(user)

    def delete_user(self, actor: User, user_id: int) -> None:
        user = self._get_other_user(actor, user_id, "No puedes eliminar tu propia cuenta desde el panel de administración")
        avatar_url = user.avatar_url
        self.users.delete(user)
        storage.delete_image(avatar_url)

    def stats(self) -> AdminStats:
        total = self.users.count()
        active = self.users.count(User.is_active.is_(True))
        return AdminStats(
            users=UserStats(
                total=total,
                active=active,
                inactive=total - active,
                by_role={role.value: self.users.count(User.role == role) for role in UserRole},
            ),
            products=self.products.count(),
            builds=self.builds.count(),
            posts=self.posts.count(),
            comments=self.comments.count(),
            pending_reports=self.reports.count(Report.status == ReportStatus.PENDING),
            advisories_by_status=self.advisories.count_by_status(),
        )

    # Moderación

    def list_comments(
        self, skip: int, limit: int, search: str | None = None, author_id: int | None = None
    ) -> PageResult[Comment]:
        items, total = self.comments.list(skip, limit, search=search, author_id=author_id)
        return PageResult(items, total, skip, limit)

    def list_reports(self, skip: int, limit: int, status: ReportStatus | None = None) -> PageResult[Report]:
        items, total = self.reports.list(skip, limit, status=status)
        return PageResult(items, total, skip, limit)

    def update_report_status(self, actor: User, report_id: int, status: ReportStatus) -> Report:
        report = self.reports.get(report_id)
        if report is None:
            raise NotFoundError("Reporte no encontrado")
        report.status = status
        if status == ReportStatus.PENDING:
            report.resolved_by_id, report.resolved_at = None, None
        else:
            report.resolved_by_id, report.resolved_at = actor.id, datetime.now(timezone.utc)
        return self.reports.save(report)

    def _get_other_user(self, actor: User, user_id: int, self_error: str) -> User:
        # Evita que un admin se quite el acceso a sí mismo y deje el sistema sin administradores
        if actor.id == user_id:
            raise ForbiddenError(self_error)
        return self.get_user(user_id)
