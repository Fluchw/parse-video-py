import json
import asyncio

from parser import parse_video_share_url, parse_video_id, VideoSource

# 根据分享链接解析
video_info = asyncio.run(parse_video_share_url("https://v.douyin.com/3TuQfg45I7M/"))
print(
    "解析分享链接：\n",
    json.dumps(video_info, ensure_ascii=False, indent=4, default=lambda x: x.__dict__),
    "\n",
)

# 根据视频id解析
# video_info = asyncio.run(
#     parse_video_id(VideoSource.DouYin, "视频ID")
# )
# print(
#     "解析视频ID：\n",
#     json.dumps(video_info, ensure_ascii=False, indent=4, default=lambda x: x.__dict__),
#     "\n",
# )