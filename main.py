from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.requests import Request


class CustomMiddleware:
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope)

        async def send_wrapper(data) -> None:
            print("hi")
            print(data)
            await send(data)

        await self.app(scope, receive, send_wrapper)


app = FastAPI(middleware=[Middleware(CustomMiddleware)])


@app.get("/")
async def home():
    ...
