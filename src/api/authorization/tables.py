from core.db.bases import Base
from sqlalchemy import INTEGER, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column


class CasbinRule(Base):
    id: Mapped[int] = mapped_column(INTEGER, primary_key=True)
    ptype: Mapped[str] = mapped_column(VARCHAR(255))
    v0: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    v1: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    v2: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    v3: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    v4: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    v5: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)

    def __str__(self) -> str:
        arr = [self.ptype]
        for v in (self.v0, self.v1, self.v2, self.v3, self.v4, self.v5):
            if v is None:
                break
            arr.append(v)
        return ", ".join(arr)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__str__()})"
