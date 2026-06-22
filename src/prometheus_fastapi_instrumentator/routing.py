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

from typing import List, Optional

from starlette.requests import HTTPConnection
from starlette.routing import Match, Mount, Route
from starlette.types import Scope


def _resolve_path(route: Route) -> Optional[str]:
    """Return the request path contributed by ``route``, or ``None`` if the
    route is a router-like wrapper whose own routes must be traversed.

    FastAPI 0.116+ (officially 0.137) wraps routers registered via
    ``app.include_router`` in an internal ``_IncludedRouter`` class that
    does not expose a ``path`` attribute. The configured mount path is
    available on ``include_context.prefix``.
    """

    if hasattr(route, "path"):
        return route.path
    include_context = getattr(route, "include_context", None)
    if include_context is not None:
        # An empty prefix means the wrapper contributes no path segment of
        # its own (e.g. ``APIRouter(prefix=...)`` registered via
        # ``include_router`` without an extra ``prefix=`` argument). The
        # caller must still recurse into nested routes.
        prefix = getattr(include_context, "prefix", "") or ""
        return prefix
    return None


def _child_routes(route: Route) -> Optional[List[Route]]:
    """Return nested routes for router-like route objects, else ``None``."""

    if isinstance(route, Mount):
        return route.routes or None
    original_router = getattr(route, "original_router", None)
    if original_router is not None and hasattr(original_router, "routes"):
        nested = list(original_router.routes)
        return nested or None
    return None


def _strip_prefix_from_scope(scope: Scope, prefix: str) -> Scope:
    """Return a copy of ``scope`` with the mount ``prefix`` removed from
    ``path``.

    ``starlette.routing.Mount.matches`` returns a child scope with the
    mount prefix already stripped. FastAPI's ``_IncludedRouter`` does
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


def _get_route_name(
    scope: Scope, routes: List[Route], route_name: Optional[str] = None
) -> Optional[str]:
    """Gets route name for given scope taking mounts into account.

    Supports plain ``Route``/``Mount`` objects as well as FastAPI's
    internal ``_IncludedRouter`` wrapper produced by
    ``app.include_router(...)``. When a matched route is a router-like
    object, the function recurses into its nested routes so the final
    label reflects the leaf endpoint.
    """

    for route in routes:
        match, child_scope = route.matches(scope)
        if match == Match.FULL:
            resolved = _resolve_path(route)
            if resolved is None:
                # Cannot produce a stable label for this route; try the
                # next candidate. Callers fall back to ``request.url.path``
                # if no route yields a name.
                continue
            route_name = resolved
            child_scope = {**scope, **child_scope}
            children = _child_routes(route)
            if children:
                # FastAPI's ``_IncludedRouter`` does not strip the mount
                # prefix from the scope before matching nested routes,
                # unlike ``starlette.routing.Mount``. Strip it here so
                # the leaf endpoint inside the included router can match.
                if not isinstance(route, Mount):
                    include_context = getattr(route, "include_context", None)
                    if include_context is not None:
                        prefix = getattr(include_context, "prefix", "") or ""
                        if prefix:
                            child_scope = _strip_prefix_from_scope(child_scope, prefix)
                child_route_name = _get_route_name(child_scope, children)
                if child_route_name is not None:
                    # Concatenate the leaf path onto the parent path so the
                    # final label is e.g. ``/api/v1/items/{item_id}`` rather
                    # than just ``/{item_id}``.
                    route_name = route_name + child_route_name
                else:
                    route_name = None
            return route_name
        elif match == Match.PARTIAL and route_name is None:
            resolved = _resolve_path(route)
            if resolved is not None:
                route_name = resolved
    return route_name


def get_route_name(request: HTTPConnection) -> Optional[str]:
    """Gets route name for given request taking mounts into account."""

    app = request.app
    scope = request.scope
    routes = app.routes
    route_name = _get_route_name(scope, routes)

    # Starlette magically redirects requests if the path matches a route name
    # with a trailing slash appended or removed. To not spam the transaction
    # names list, we do the same here and put these redirects all in the
    # same "redirect trailing slashes" transaction name.
    if not route_name and app.router.redirect_slashes and scope["path"] != "/":
        redirect_scope = dict(scope)
        if scope["path"].endswith("/"):
            redirect_scope["path"] = scope["path"][:-1]
            trim = True
        else:
            redirect_scope["path"] = scope["path"] + "/"
            trim = False

        route_name = _get_route_name(redirect_scope, routes)
        if route_name is not None:
            route_name = route_name.rstrip("/")
            route_name = route_name + "/" if trim else route_name
    return route_name
