# BSD 3-Clause License
#
# Copyright (c) 2012, the Sentry Team, see AUTHORS for more details
# Copyright (c) 2019, Elasticsearch BV
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE

"""Helper module for routing.

The two functions in this module are licensed under the BSD 3-Clause License
instead of the ISC License like the rest of the project. Therefore the code
is contained in a dedicated module.

Based on code from [elastic/apm-agent-python](https://github.com/elastic/apm-agent-python/blob/527f62c0c50842f94ef90fda079853372539319a/elasticapm/contrib/starlette/__init__.py).
"""

from typing import List, Optional, Tuple

from starlette.requests import HTTPConnection
from starlette.routing import Match, Mount, Route
from starlette.types import Scope


def _inspect_route(route: Route) -> Tuple[Optional[str], Optional[List[Route]]]:
    """Describe how `route` contributes to a resolved route name.

    Returns a `(path, children)` tuple where `path` is the URL segment the
    route contributes (or `None` if the route cannot yield a stable label and
    should be skipped) and `children` are the nested routes to recurse into
    for router-like routes (or `None` for leaf routes).

    Three route shapes are handled:

    * A plain `Route` leaf exposes `path` and has no children.
    * A `Mount` exposes `path` and nests `routes`. Its `matches()`
      already strips the mount prefix from the returned child scope.
    * FastAPI's `_IncludedRouter` (0.116+, officially 0.137) has no `path`
      attribute; its prefix lives on `include_context.prefix` and its
      children on `original_router.routes`. Its `matches()` does not strip
      the prefix, so the caller must strip it before recursing.
    """

    # Path segment contributed by the route.
    if hasattr(route, "path"):
        path: Optional[str] = route.path
    else:
        include_context = getattr(route, "include_context", None)
        # An empty prefix means the wrapper contributes no path segment of its
        # own (e.g. `APIRouter(prefix=...)` registered via `include_router`
        # without an extra `prefix=` argument); the caller still recurses.
        if include_context is None:
            path = None
        else:
            path = getattr(include_context, "prefix", "") or ""

    # Nested routes to recurse into, if this is a router-like route.
    if isinstance(route, Mount):
        children: Optional[List[Route]] = route.routes or None
    else:
        original_router = getattr(route, "original_router", None)
        if original_router is not None and hasattr(original_router, "routes"):
            children = list(original_router.routes) or None
        else:
            children = None

    return path, children


def _strip_prefix_from_scope(scope: Scope, prefix: str) -> Scope:
    """Return a copy of `scope` with the mount `prefix` removed from
    `path`.

    `starlette.routing.Mount.matches` returns a child scope with the
    mount prefix already stripped. FastAPI's `_IncludedRouter` does
    not, so the recursion into the included router's own routes would
    never match a leaf endpoint. Stripping the prefix here restores the
    behaviour expected by the recursive call.
    """

    if not prefix:
        return scope
    path = scope.get("path", "") or ""
    if path == prefix:
        return {**scope, "path": ""}
    if path.startswith(prefix + "/"):
        return {**scope, "path": path.removeprefix(prefix)}
    return scope


def _descend_into_included_router(scope: Scope, prefix: str) -> Scope:
    """Return a child scope for recursing into an `_IncludedRouter`.

    Unlike `starlette.routing.Mount`, FastAPI's `_IncludedRouter` (0.116+)
    neither advances `root_path` nor strips its own prefix when it matches,
    so nested leaf routes would never match on their own.

    Starlette resolves a route against `path` minus `root_path` (see
    `starlette._utils.get_route_path`). When the included router is reached
    through a mounted sub-app, a parent `Mount` has already set a non-empty
    `root_path` while leaving `path` untouched, so stripping `prefix` from
    `path` directly (as for a top-level included router) silently fails.

    This helper computes the request path relative to the current `root_path`,
    removes the router `prefix`, and returns a scope whose `path` is that
    remainder with `root_path` reset, so nested route matching resolves the
    leaf endpoint regardless of whether the router sits behind a mount.
    """

    root_path = scope.get("root_path", "") or ""
    path = scope.get("path", "") or ""

    # Request path relative to the current root_path, mirroring Starlette's
    # `get_route_path` semantics.
    if (
        root_path
        and path.startswith(root_path)
        and (path == root_path or path[len(root_path)] == "/")
    ):
        route_path = path[len(root_path) :]
    else:
        route_path = path

    if prefix:
        if route_path == prefix:
            route_path = ""
        elif route_path.startswith(prefix + "/"):
            route_path = route_path.removeprefix(prefix)
        # Otherwise the prefix is not present; leave route_path unchanged as a
        # safe fallback so the caller can still attempt to match nested routes.

    return {**scope, "path": route_path, "root_path": ""}


def _normalize_root_path(root_path: str) -> str:
    """Return root_path in canonical form.

    Canonical form is empty string for "no root path", "/" for root,
    otherwise a leading slash with no trailing slash.
    """

    if not root_path:
        return ""
    if root_path == "/":
        return "/"
    return "/" + root_path.strip("/")


def _effective_root_path(scope: Scope, app_root_path: str) -> str:
    """Resolve which root_path to use for matching and labels.

    For app-level root_path deployments, trust `scope["root_path"]` when
    present because servers may normalize it differently (e.g. trailing slash).
    If app has no root_path configured, ignore scope root_path to avoid
    treating mount prefixes as deployment root paths.
    """

    app_root_path = _normalize_root_path(app_root_path)
    if not app_root_path:
        return ""
    scope_root_path = _normalize_root_path((scope.get("root_path", "") or ""))
    return scope_root_path or app_root_path


def _prepend_root_path(route_name: str, scope: Scope, root_path: str) -> str:
    """Prepend `root_path` to a resolved templated `route_name`."""

    root_path = _normalize_root_path(root_path)
    if not root_path:
        return route_name

    path = scope.get("path", "") or ""
    if path != root_path and not path.startswith(root_path + "/"):
        return route_name

    normalized_root = root_path
    if route_name == normalized_root or route_name.startswith(normalized_root + "/"):
        return route_name

    if route_name == "/":
        return normalized_root + "/"
    return normalized_root + route_name


def _get_route_name(
    scope: Scope, routes: List[Route], route_name: Optional[str] = None
) -> Optional[str]:
    """Gets route name for given scope taking mounts into account.

    Supports plain `Route`/`Mount` objects as well as FastAPI's internal
    `_IncludedRouter` wrapper produced by `app.include_router(...)`. When a
    matched route is router-like, the function recurses into its nested routes
    so the final label reflects the leaf endpoint, e.g.
    `/api/v1/items/{item_id}` rather than just `/{item_id}`.
    """

    for route in routes:
        match, child_scope = route.matches(scope)

        if match == Match.FULL:
            path, children = _inspect_route(route)
            if path is None:
                # Cannot produce a stable label for this route; try the next
                # candidate. Callers fall back to `request.url.path` if no
                # route yields a name.
                continue

            if not children:
                return path

            child_scope = {**scope, **child_scope}
            if not isinstance(route, Mount):
                # Unlike `Mount`, `_IncludedRouter` neither advances
                # `root_path` nor strips its prefix from the child scope, so
                # descend into it here so the nested leaf endpoint can match.
                # `path` is that prefix.
                child_scope = _descend_into_included_router(child_scope, path)

            nested_name = _get_route_name(child_scope, children)
            if nested_name is None:
                return None
            return path + nested_name

        if match == Match.PARTIAL and route_name is None:
            path, _ = _inspect_route(route)
            if path is not None:
                route_name = path

    return route_name


def get_route_name(request: HTTPConnection) -> Optional[str]:
    """Gets route name for given request taking mounts into account."""

    app = request.app
    scope = request.scope
    app_root_path = getattr(app, "root_path", "") or ""
    # `_effective_root_path` already returns a normalized root path, so it can
    # be stripped from the scope directly for route matching.
    root_path = _effective_root_path(scope, app_root_path)
    lookup_scope = _strip_prefix_from_scope(scope, root_path)
    routes = app.routes
    route_name = _get_route_name(lookup_scope, routes)

    # Starlette magically redirects requests if the path matches a route name
    # with a trailing slash appended or removed. To not spam the transaction
    # names list, we do the same here and put these redirects all in the
    # same "redirect trailing slashes" transaction name.
    if not route_name and app.router.redirect_slashes and lookup_scope["path"] != "/":
        redirect_scope = dict(lookup_scope)
        if lookup_scope["path"].endswith("/"):
            redirect_scope["path"] = lookup_scope["path"][:-1]
            trim = True
        else:
            redirect_scope["path"] = lookup_scope["path"] + "/"
            trim = False

        route_name = _get_route_name(redirect_scope, routes)
        if route_name is not None:
            route_name = route_name.rstrip("/")
            route_name = route_name + "/" if trim else route_name

    if route_name is not None:
        route_name = _prepend_root_path(route_name, scope, root_path)
    return route_name
