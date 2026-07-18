from typing import Any, List, Optional

from starlette.requests import HTTPConnection
from starlette.routing import BaseRoute, Match, Mount
from starlette.types import Scope


def _effective_routes(routes: List[BaseRoute]) -> List[BaseRoute]:
    """Flattens a list of routes into directly matchable routes.

    FastAPI (>= 0.116) represents routers registered via `include_router`
    with an internal `_IncludedRouter` object that has no `path` attribute
    and does not expose its children via the `matches` API. Such routers do
    expose `effective_route_contexts()` though, which yields context objects
    whose resolved route already carries the fully prefixed `path`. Every
    other route is passed through unchanged.
    """

    effective: List[BaseRoute] = []
    for route in routes:
        contexts: Any = getattr(route, "effective_route_contexts", None)
        if callable(contexts):
            resolved_contexts: Any = contexts()
            for context in resolved_contexts:
                # Mounts must be recursed into, so the mount object (which
                # carries the fully prefixed path and its sub-routes) is used.
                # Plain Starlette routes expose their fully prefixed path via
                # `starlette_route`. FastAPI routes keep `starlette_route`
                # unset but the context itself is matchable and carries the
                # fully prefixed `path`.
                starlette_route = getattr(context, "starlette_route", None)
                if starlette_route is not None:
                    effective.append(starlette_route)
                else:
                    effective.append(context)
        else:
            effective.append(route)
    return effective


def _get_route_name(scope: Scope, routes: List[BaseRoute]) -> Optional[str]:
    """Resolves the templated handler for a scope against a list of routes.

    Matching relies on Starlette's own `matches` implementation, which
    resolves the path relative to `scope["root_path"]`. Mounts are recursed
    into with the child scope so their prefix is prepended to the result. A
    full match wins immediately, a partial match (e.g. path matches but method
    does not) is remembered as a fallback.
    """

    partial: Optional[str] = None

    for route in _effective_routes(routes):
        match, child_scope = route.matches(scope)
        if match == Match.NONE:
            continue

        if isinstance(route, Mount):
            sub_routes = route.routes
            if not sub_routes:
                # Opaque mounted ASGI app without introspectable sub-routes.
                # The mount path itself is the most specific handler available.
                name = route.path
            else:
                child = _get_route_name({**scope, **child_scope}, sub_routes)
                if child is None:
                    continue
                name = route.path + child
        else:
            path = getattr(route, "path", None)
            if path is None:
                continue
            name = path

        if match == Match.FULL:
            return name
        if partial is None:
            partial = name

    return partial


def get_route_name(
    request: HTTPConnection, should_include_root_path: bool
) -> Optional[str]:
    """Gets route name.

    Resolves the templated route for the given request, e.g. `/api/items/123`
    maps to `/api/items/{item_id}`. Returns `None` when no route matches.

    Works with both plain Starlette and FastAPI applications and supports
    router prefixes, `include_router` (including nested routers), mounted
    sub-applications and `root_path`. When the application itself is a mounted
    sub-application that is instrumented directly, the resolved name is relative
    to that sub-application.

    Args:
        request: Connection whose scope should be resolved to a route name.
        should_include_root_path: Whether the returned route name should be
            prefixed with the application's effective `root_path`.
    """

    scope = request.scope
    app = scope.get("app")
    routes = getattr(app, "routes", None)
    if not routes:
        return None

    name = _get_route_name(scope, routes)

    if name is not None:
        if not should_include_root_path:
            return name

        # Only the application's own `root_path` is prepended. A `root_path`
        # injected into the scope by a parent mount (i.e. when a mounted
        # sub-application is instrumented directly) is intentionally ignored so
        # the resolved name stays relative to that sub-application.
        root_path = getattr(app, "root_path", "") or ""
        if root_path:
            return root_path.rstrip("/") + name
        return name

    # No route matched. If the router redirects on trailing slashes, a request
    # like `/items` against a route `/items/` (or vice versa) does not match
    # directly but would be redirected. Report the requested path in that case.
    router = getattr(app, "router", None)
    if router is not None and getattr(router, "redirect_slashes", False):
        path = scope.get("path", "")
        toggled = path[:-1] if path.endswith("/") else path + "/"
        if toggled and toggled != path:
            if _get_route_name({**scope, "path": toggled}, routes) is not None:
                return path

    return None
