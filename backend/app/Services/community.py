from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.Models.community import Comment, Post, Report
from app.Models.user import User
from app.Repository.build_repository import BuildRepository
from app.Repository.community_repository import CommentRepository, PostRepository, ReportRepository
from app.Schema.common_schema import PageResult, update_data
from app.Schema.community_schema import CommentCreate, CommentUpdate, PostCreate, PostUpdate, ReportCreate


class CommunityService:
    def __init__(self, db: Session):
        self.posts = PostRepository(db)
        self.comments = CommentRepository(db)
        self.builds = BuildRepository(db)
        self.reports = ReportRepository(db)

    # Publicaciones

    def list_posts(
        self, skip: int, limit: int, search: str | None = None, author_id: int | None = None
    ) -> PageResult[Post]:
        items, total = self.posts.list(skip, limit, search=search, author_id=author_id)
        return PageResult(items, total, skip, limit)

    def get_post(self, post_id: int) -> Post:
        post = self.posts.get(post_id)
        if post is None:
            raise NotFoundError("Publicación no encontrada")
        return post

    def create_post(self, author: User, data: PostCreate) -> Post:
        self._validate_build(data.build_id)
        return self.posts.add(Post(author_id=author.id, **data.model_dump()))

    def update_post(self, post_id: int, user: User, data: PostUpdate) -> Post:
        post = self.get_post(post_id)
        if post.author_id != user.id:
            raise ForbiddenError("Solo puedes editar tus propias publicaciones")
        changes = update_data(data, {"build_id"})
        if "build_id" in changes:
            self._validate_build(changes["build_id"])
        for field, value in changes.items():
            setattr(post, field, value)
        return self.posts.save(post)

    def delete_post(self, post_id: int, user: User) -> None:
        post = self.get_post(post_id)
        self._ensure_author_or_admin(post.author_id, user, "Solo puedes eliminar tus propias publicaciones")
        self.posts.delete(post)

    def like_post(self, post_id: int, user: User) -> Post:
        post = self.get_post(post_id)
        # El commit expira el objeto, así que like_count se recalcula al leerlo
        if self.posts.get_like(post_id, user.id) is None:
            self.posts.add_like(post_id, user.id)
        return post

    def unlike_post(self, post_id: int, user: User) -> Post:
        post = self.get_post(post_id)
        like = self.posts.get_like(post_id, user.id)
        if like is not None:
            self.posts.remove_like(like)
        return post

    # Comentarios

    def list_comments(self, post_id: int, skip: int, limit: int) -> PageResult[Comment]:
        self.get_post(post_id)
        items, total = self.comments.list_by_post(post_id, skip, limit)
        return PageResult(items, total, skip, limit)

    def add_comment(self, post_id: int, author: User, data: CommentCreate) -> Comment:
        self.get_post(post_id)
        return self.comments.add(Comment(post_id=post_id, author_id=author.id, content=data.content))

    def update_comment(self, comment_id: int, user: User, data: CommentUpdate) -> Comment:
        comment = self._get_comment(comment_id)
        if comment.author_id != user.id:
            raise ForbiddenError("Solo puedes editar tus propios comentarios")
        comment.content = data.content
        return self.comments.save(comment)

    def delete_comment(self, comment_id: int, user: User) -> None:
        comment = self._get_comment(comment_id)
        self._ensure_author_or_admin(comment.author_id, user, "Solo puedes eliminar tus propios comentarios")
        self.comments.delete(comment)

    # Reportes

    def report_post(self, post_id: int, reporter: User, data: ReportCreate) -> Report:
        self.get_post(post_id)
        if self.reports.has_pending(reporter.id, post_id=post_id):
            raise ConflictError("Ya reportaste esta publicación; un administrador lo revisará")
        return self.reports.add(Report(reporter_id=reporter.id, post_id=post_id, reason=data.reason))

    def report_comment(self, comment_id: int, reporter: User, data: ReportCreate) -> Report:
        self._get_comment(comment_id)
        if self.reports.has_pending(reporter.id, comment_id=comment_id):
            raise ConflictError("Ya reportaste este comentario; un administrador lo revisará")
        return self.reports.add(Report(reporter_id=reporter.id, comment_id=comment_id, reason=data.reason))

    # Auxiliares

    def _get_comment(self, comment_id: int) -> Comment:
        comment = self.comments.get(comment_id)
        if comment is None:
            raise NotFoundError("Comentario no encontrado")
        return comment

    def _validate_build(self, build_id: int | None) -> None:
        if build_id is None:
            return
        build = self.builds.get(build_id)
        if build is None or not build.is_public:
            raise BadRequestError("Solo puedes compartir builds públicas")

    @staticmethod
    def _ensure_author_or_admin(author_id: int, user: User, message: str) -> None:
        # El admin puede moderar (eliminar) contenido de cualquier usuario
        if author_id != user.id and not user.is_admin:
            raise ForbiddenError(message)
