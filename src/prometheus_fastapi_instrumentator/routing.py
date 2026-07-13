from typing import List, Optional, Tuple

from starlette.requests import HTTPConnection
from starlette.routing import Match, Mount, Route
from starlette.types import Scope

def get_route_name(request: HTTPConnection) -> Optional[str]:
    """Gets route name."""
