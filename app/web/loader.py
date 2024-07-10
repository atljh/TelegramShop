from aiohttp import web

app = web.Application()

@web.middleware
async def middleware(request, handler):
    resp: web.Response = await handler(request)
    try:
        resp.headers.add("Cache-Control", "no-cache, no-store, must-revalidate")
        resp.headers.add("Pragma", "no-cache")
        resp.headers.add("Expires", "0")
        return resp
    except Exception as e:
        pass

app.middlewares.append(middleware)


