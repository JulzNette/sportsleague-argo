"""
Import every model here so app.db.base.Base.metadata is fully populated
for Alembic autogenerate and for create_all() in local/dev scripts.
"""
from app.models.stub import Organization, User  # noqa: F401 - sandbox stub only
from app.models.league import League  # noqa: F401
from app.models.season import Season  # noqa: F401
from app.models.division import Division  # noqa: F401
from app.models.team import Team  # noqa: F401
from app.models.player import Player  # noqa: F401
from app.models.referee import Referee  # noqa: F401
from app.models.match import Match  # noqa: F401
from app.models.match_result import MatchResult  # noqa: F401
from app.models.report import Report  # noqa: F401
