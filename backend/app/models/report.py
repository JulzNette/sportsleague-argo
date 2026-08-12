import uuid
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, OrgAuditMixin


class Report(OrgAuditMixin, Base):
    """
    Stores only report *metadata* (what was requested, by whom, scoped to
    which season/division). The report's actual content (standings, stats)
    is always recomputed on view/export from live data - never cached here -
    per the "never store derived values" rule.
    """
    __tablename__ = "sportsleague_reports"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Season Summary | Match Report | Team Statistics | Referee Activity
    season_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    division_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    generated_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
