import os
import re
import secrets
from parser import VideoSource, parse_video_id, parse_video_share_url

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from fastapi_mcp import FastApiMCP

app = FastAPI()

mcp = FastApiMCP(app)

mcp.mount_http()

templates = Jinja2Templates(directory="templates")


def format_duration(milliseconds: int) -> str:
    """格式化视频时长，如 '1:30' 或 '1:05:30'"""
    if not milliseconds:
        return "0:00"
    seconds = milliseconds // 1000
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_video_info(video_info) -> dict:
    """格式化视频信息，添加时长相关字段"""
    data = video_info.__dict__.copy()
    
    # 添加时长格式化字段
    duration = data.get("duration", 0)
    data["duration_seconds"] = round(duration / 1000, 2) if duration else 0
    data["duration_formatted"] = format_duration(duration)
    
    return data


def get_auth_dependency() -> list[Depends]:
    """
    根据环境变量动态返回 Basic Auth 依赖项
    - 如果设置了 USERNAME 和 PASSWORD，返回验证函数
    - 如果未设置，返回一个直接返回 None 的 Depends
    """
    basic_auth_username = os.getenv("PARSE_VIDEO_USERNAME")
    basic_auth_password = os.getenv("PARSE_VIDEO_PASSWORD")

    if not (basic_auth_username and basic_auth_password):
        return []  # 返回包含Depends实例的列表

    security = HTTPBasic()

    def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
        # 验证凭据
        correct_username = secrets.compare_digest(
            credentials.username, basic_auth_username
        )
        correct_password = secrets.compare_digest(
            credentials.password, basic_auth_password
        )
        if not (correct_username and correct_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Basic"},
            )
        return credentials

    return [Depends(verify_credentials)]  # 返回封装好的 Depends


@app.get("/", response_class=HTMLResponse, dependencies=get_auth_dependency())
async def read_item(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "github.com/wujunwei928/parse-video-py Demo",
        },
    )


@app.get("/video/share/url/parse", dependencies=get_auth_dependency())
async def share_url_parse(url: str):
    url_reg = re.compile(r"http[s]?:\/\/[\w.-]+[\w\/-]*[\w.-]*\??[\w=&:\-\+\%]*[/]*")
    video_share_url = url_reg.search(url).group()

    try:
        video_info = await parse_video_share_url(video_share_url)
        return {"code": 200, "msg": "解析成功", "data": format_video_info(video_info)}
    except Exception as err:
        return {
            "code": 500,
            "msg": str(err),
        }


@app.get("/video/id/parse", dependencies=get_auth_dependency())
async def video_id_parse(source: VideoSource, video_id: str):
    try:
        video_info = await parse_video_id(source, video_id)
        return {"code": 200, "msg": "解析成功", "data": format_video_info(video_info)}
    except Exception as err:
        return {
            "code": 500,
            "msg": str(err),
        }


mcp.setup_server()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8965)