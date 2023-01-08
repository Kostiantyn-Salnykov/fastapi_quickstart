from sqlalchemy import SMALLINT, VARCHAR, Column, ForeignKey
from sqlalchemy.orm import relationship

from apps.CORE.db import Base, CreatedAtMixin, CreatedUpdatedMixin, UUIDMixin
from apps.users.models import User
from apps.wishmaster.enums import WishComplexities, WishPriorities, WishStatuses

CASCADES = {"ondelete": "CASCADE", "onupdate": "CASCADE"}


class WishList(Base, UUIDMixin, CreatedUpdatedMixin):
    title = Column(VARCHAR(length=128), nullable=False, index=True)
    owner_id = Column(ForeignKey(column="user.id", **CASCADES), nullable=False)

    wishes = relationship(
        "Wish",
        cascade="all, delete",
        primaryjoin="Wish.wishlist_id == WishList.id",
        back_populates="wishlist",
        order_by="desc(Wish.priority), desc(Wish.created_at)",
    )
    owner = relationship(User, cascade="all, delete", backref="wishlists")

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(title="{self.title}")'


class Category(Base, UUIDMixin, CreatedUpdatedMixin):
    title = Column(VARCHAR(length=128), nullable=False, index=True)
    owner_id = Column(ForeignKey(column="user.id", **CASCADES), nullable=False)

    owner = relationship(User, backref="categories")

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(title="{self.title}", owner_id="{self.owner_id}")'


class Wish(Base, UUIDMixin, CreatedUpdatedMixin):
    wishlist_id = Column(ForeignKey(column="wish_list.id", **CASCADES), nullable=False)
    category_id = Column(ForeignKey(column="category.id", **CASCADES))
    title = Column(VARCHAR(length=128), nullable=False, index=True)
    description = Column(VARCHAR(length=256))
    status = Column(VARCHAR(length=32), default=WishStatuses.CREATED.value, nullable=False)
    complexity = Column(VARCHAR(length=32), default=WishComplexities.NORMAL.value, nullable=False)
    priority = Column(SMALLINT, default=WishPriorities.NORMAL.value, nullable=False)

    wishlist = relationship(
        "WishList",
        cascade="all, delete",
        primaryjoin="Wish.wishlist_id == WishList.id",
        back_populates="wishes",
        order_by="desc(Wish.priority), desc(Wish.created_at)",
    )
    category = relationship("Category", sync_backref=False, lazy="joined")
    tags = relationship(
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
    title = Column(VARCHAR(length=64), nullable=False, index=True)

    def __init__(self, title: str) -> None:
        self.title = title

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(title="{self.title}")'


class WishTag(Base, CreatedAtMixin):
    wish_id = Column(ForeignKey(column="wish.id", **CASCADES), primary_key=True)
    tag_id = Column(ForeignKey(column="tag.id", **CASCADES), primary_key=True)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(wish_id="{self.wish_id}", tag_id="{self.tag_id}")'
