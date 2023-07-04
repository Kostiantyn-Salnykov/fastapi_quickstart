import uuid

from sqlalchemy import SMALLINT, VARCHAR, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.CORE.db import Base, CreatedAtMixin, CreatedUpdatedMixin, UUIDMixin
from apps.CORE.models import CASCADES, User
from apps.CORE.types import StrOrNone
from apps.wishmaster.enums import WishComplexities, WishPriorities, WishStatuses


class WishList(Base, UUIDMixin, CreatedUpdatedMixin):
    title: Mapped[str] = mapped_column(VARCHAR(length=128), nullable=False, index=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(column="user.id", **CASCADES), nullable=False)

    wishes: Mapped[list["Wish"]] = relationship(
        "Wish",
        cascade="all, delete",
        primaryjoin="Wish.wishlist_id == WishList.id",
        back_populates="wishlist",
        order_by="desc(Wish.priority), desc(Wish.created_at)",
    )
    owner: Mapped["User"] = relationship(User, cascade="all, delete", backref="wishlists")

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(title="{self.title}")'


class Category(Base, UUIDMixin, CreatedUpdatedMixin):
    title: Mapped[str] = mapped_column(VARCHAR(length=128), nullable=False, index=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(column="user.id", **CASCADES), nullable=False)

    owner: Mapped["User"] = relationship(User, backref="categories")

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(title="{self.title}", owner_id="{self.owner_id}")'


class Wish(Base, UUIDMixin, CreatedUpdatedMixin):
    wishlist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(column="wish_list.id", **CASCADES), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey(column="category.id", **CASCADES))
    title: Mapped[str] = mapped_column(VARCHAR(length=128), nullable=False, index=True)
    description: Mapped[StrOrNone] = mapped_column(VARCHAR(length=255))
    status: Mapped[str] = mapped_column(VARCHAR(length=32), default=WishStatuses.CREATED.value, nullable=False)
    complexity: Mapped[str] = mapped_column(VARCHAR(length=32), default=WishComplexities.NORMAL.value, nullable=False)
    priority: Mapped[int] = mapped_column(SMALLINT, default=WishPriorities.NORMAL.value, nullable=False)

    wishlist: Mapped["WishList"] = relationship(
        "WishList",
        cascade="all, delete",
        primaryjoin="Wish.wishlist_id == WishList.id",
        back_populates="wishes",
        order_by="desc(Wish.priority), desc(Wish.created_at)",
    )
    category: Mapped["Category"] = relationship("Category", sync_backref=False, lazy="joined")
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary="wish_tag",
        cascade="all, delete",
        collection_class=set,
        sync_backref=False,
        lazy="joined",
    )

    # TODO update
    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}(title="{self.title}", description="{self.description}", status="{self.status}")'
        )


class Tag(Base, UUIDMixin, CreatedAtMixin):
    title: Mapped[str] = mapped_column(VARCHAR(length=64), nullable=False, index=True)

    def __init__(self, title: str) -> None:
        self.title = title

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(title="{self.title}")'


class WishTag(Base, CreatedAtMixin):
    wish_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(column="wish.id", **CASCADES), primary_key=True)
    tag_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(column="tag.id", **CASCADES), primary_key=True)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(wish_id="{self.wish_id}", tag_id="{self.tag_id}")'
