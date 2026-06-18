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

import logging
from typing import Any, List, Optional

from starlette.requests import HTTPConnection
from starlette.routing import BaseRoute, Match, Mount
from starlette.types import Scope

logger = logging.getLogger(__name__)


def _effective_route_path(ctx: Any, scope: Scope, child_scope: Scope) -> Optional[str]:
    """Resolve the full, prefixed path for a matched FastAPI
    ``_EffectiveRouteContext``.

    For ``APIRoute`` contexts the prefixed path is on ``ctx.path`` (and
    ``ctx.starlette_route`` is ``None``). For ``Mount`` and websocket contexts
    ``ctx.path`` is ``""`` and the prefixed path is carried by
    ``ctx.starlette_route`` instead; mounts are recursed into so the mounted
    sub-route name is appended, matching the handling of top-level mounts.
    """
    underlying = getattr(ctx, "starlette_route", None)
    if underlying is None:
        return getattr(ctx, "path", None)
    if isinstance(underlying, Mount) and underlying.routes:
        child_route_name = _get_route_name(
            {**scope, **child_scope}, underlying.routes, underlying.path
        )
        if child_route_name is None:
            return None
        return underlying.path + child_route_name
    return getattr(underlying, "path", None)


def _get_route_name(
    scope: Scope, routes: List[BaseRoute], route_name: Optional[str] = None
) -> Optional[str]:
    """Gets route name for given scope, taking mounts and included routers
    into account."""

    for route in routes:
        # FastAPI (>= 0.137) wraps every ``include_router(...)`` in a private
        # ``_IncludedRouter`` -- a ``BaseRoute`` *without* a ``path``, so the
        # generic ``route.path`` accesses below would raise ``AttributeError``
        # (#370) on both full and partial (e.g. 405) matches. Resolve it via
        # its ``effective_route_contexts()``, whose contexts expose the fully
        # prefixed path. Detected by duck typing so this library still works
        # with plain Starlette (which never has it); guarded broadly so that a
        # future FastAPI internals change degrades to no route label rather
        # than turning every request into a 500.
        effective_contexts = getattr(route, "effective_route_contexts", None)
        if callable(effective_contexts):
            try:
                for ctx in effective_contexts():
                    ctx_match, ctx_child_scope = ctx.matches(scope)
                    if ctx_match == Match.FULL:
                        return _effective_route_path(ctx, scope, ctx_child_scope)
            except Exception:
                logger.debug(
                    "Could not resolve route name from an included router; "
                    "falling back to no route label.",
                    exc_info=True,
                )
            continue

        match, child_scope = route.matches(scope)
        if match == Match.FULL:
            if isinstance(route, Mount) and route.routes:
                child_route_name = _get_route_name(
                    {**scope, **child_scope}, route.routes, route.path
                )
                if child_route_name is None:
                    return None
                return route.path + child_route_name
            return getattr(route, "path", None)
        elif match == Match.PARTIAL and route_name is None:
            route_name = getattr(route, "path", None)
    return None


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
            route_name = route_name + "/" if trim else route_name[:-1]
    return route_name
