import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import StreamingResponse
from starlette.background import BackgroundTask
from urllib.parse import urlparse

client = httpx.AsyncClient()

app = FastAPI()

allow_all = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=allow_all, allow_credentials=True, allow_methods=allow_all, allow_headers=allow_all)

async def _reverse_proxy(request: Request):
    path = request.url.path.lstrip("/")
    url = httpx.URL(url=path,
                    query=request.url.query.encode("utf-8"))

    headers = request.headers.mutablecopy()
    rp_req = client.build_request(request.method, url, content=await request.body()) # headers=headers

    rp_resp = await client.send(rp_req, stream=True)
    return StreamingResponse(
        rp_resp.aiter_raw(),
        status_code=rp_resp.status_code,
        headers=rp_resp.headers,
        background=BackgroundTask(rp_resp.aclose),
    )


app.add_route("/{path:path}", _reverse_proxy, ["GET", "POST"])


if __name__ == "__main__":
    uvicorn.run("main:app")