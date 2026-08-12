from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, OrgAuditMixin


class Referee(OrgAuditMixin, Base):
    __tablename__ = "sportsleague_referees"
    __table_args__ = (
        UniqueConstraint("organization_id", "license_number", name="uq_sportsleague_referees_org_license"),
    )

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    license_number: Mapped[str] = mapped_column(String(64), nullable=False)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Active")
    # Active | Inactive | Suspended
