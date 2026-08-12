import uuid
from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, OrgAuditMixin


class League(OrgAuditMixin, Base):
    __tablename__ = "sportsleague_leagues"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_sportsleague_leagues_org_name"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sport_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Active")
    # Active | Archived

    seasons: Mapped[list["Season"]] = relationship(back_populates="league", cascade="all, delete-orphan")
