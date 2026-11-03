from __future__ import annotations

from sqlalchemy import exists, or_, select

from app.Models.community import Comment, Post, PostLike, Report, ReportStatus
from app.Repository.base_repository import BaseRepository


class PostRepository(BaseRepository[Post]):
    model = Post

    def list(
        self, skip: int, limit: int, search: str | None = None, author_id: int | None = None
    ) -> tuple[list[Post], int]:
        stmt = select(Post).order_by(Post.created_at.desc(), Post.id.desc())
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(Post.title.ilike(pattern), Post.content.ilike(pattern)))
        if author_id is not None:
            stmt = stmt.where(Post.author_id == author_id)
        return self.paginate(stmt, skip, limit)

    def get_like(self, post_id: int, user_id: int) -> PostLike | None:
        return self.db.get(PostLike, (post_id, user_id))

    def add_like(self, post_id: int, user_id: int) -> None:
        self.db.add(PostLike(post_id=post_id, user_id=user_id))
        self.db.commit()

    def remove_like(self, like: PostLike) -> None:
        self.db.delete(like)
        self.db.commit()


class CommentRepository(BaseRepository[Comment]):
    model = Comment

    def list_by_post(self, post_id: int, skip: int, limit: int) -> tuple[list[Comment], int]:
        stmt = select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at, Comment.id)
        return self.paginate(stmt, skip, limit)

    def list(
        self, skip: int, limit: int, search: str | None = None, author_id: int | None = None
    ) -> tuple[list[Comment], int]:
        stmt = select(Comment).order_by(Comment.created_at.desc(), Comment.id.desc())
        if search:
            stmt = stmt.where(Comment.content.ilike(f"%{search}%"))
        if author_id is not None:
            stmt = stmt.where(Comment.author_id == author_id)
        return self.paginate(stmt, skip, limit)


class ReportRepository(BaseRepository[Report]):
    model = Report

    def list(self, skip: int, limit: int, status: ReportStatus | None = None) -> tuple[list[Report], int]:
        stmt = select(Report).order_by(Report.created_at.desc(), Report.id.desc())
        if status is not None:
            stmt = stmt.where(Report.status == status)
        return self.paginate(stmt, skip, limit)

    def has_pending(self, reporter_id: int, post_id: int | None = None, comment_id: int | None = None) -> bool:
        return bool(self.db.scalar(select(exists().where(
            Report.reporter_id == reporter_id,
            Report.status == ReportStatus.PENDING,
            Report.post_id == post_id if post_id is not None else Report.post_id.is_(None),
            Report.comment_id == comment_id if comment_id is not None else Report.comment_id.is_(None),
        ))))
