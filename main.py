"""
Author: Vincent Yang
Date: 2024-03-04 04:48:39
LastEditors: Vincent Yang
LastEditTime: 2024-03-04 06:16:32
FilePath: /DouyinLiveRecorder/getStreamLink.py
Telegram: https://t.me/missuo
GitHub: https://github.com/missuo

Copyright © 2024 by Vincent, All Rights Reserved. 
"""

import http
from seleniumbase import Driver
import re
import json
import urllib.request
from typing import Dict, Any
import execjs
from flask import Flask, jsonify, request, abort
from flask_cors import CORS

no_proxy_handler = urllib.request.ProxyHandler({})
opener = urllib.request.build_opener(no_proxy_handler)


def get_douyin_stream_data(url: str) -> Dict[str, Any]:
    # cookies = get_cookies() # if cookies expire
    # print(cookies)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Referer": "https://live.douyin.com/",
        "Cookie": "FORCE_LOGIN=%7B%22videoConsumedRemainSeconds%22%3A180%7D; volume_info=%7B%22isMute%22%3Afalse%2C%22isUserMute%22%3Afalse%2C%22volume%22%3A0.6%7D; xgplayer_user_id=70600190527; live_use_vvc=%22false%22; live_can_add_dy_2_desktop=%220%22; csrf_session_id=0cfc6cb9aa2f9b6d177256db1f21114e; webcast_local_quality=null; msToken=-m8Q49jOIaxWHpFhhtoJv33qSFBW-B6lJIbAnK9017IEbaFgwO88idv5crAT8_HxcjpfIBl7yTfJxbucjC-IouZW6TwnyaxtumM4Oo3i; device_web_memory_size=8; msToken=WA2i_vUwETUH8sxKT5Ery7Q_W-ZziC7KrPZs7nlpaZik5S-KJJ7oL60LcD6Ibmm8WnO1-t5A0yG8wQPgwy-J5MPtrs7q2p-FJu-VswTu; __ac_nonce=065e5ace3008399096380; device_web_cpu_core=10; __ac_signature=_02B4Z6wo00f01AVe13AAAIDAxv2odXozCHQFfvPAAGS433; IsDouyinActive=true; __live_version__=%221.1.1.8422%22; ttwid=1%7CToDImUVmkBIdeSr9GGAtlW-cvyq5G23v5o63vhdEe-A%7C1709550820%7Cbeb9fa8039073ad07ab322ecbe575a444ac27c733d6cb85e2f88ad8b0f588590; has_avx2=null",
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        response = opener.open(req, timeout=15)
        html_str = response.read().decode("utf-8")
        match_json_str = re.search(r'(\{\\"state\\":.*?)]\\n"]\)', html_str)
        if not match_json_str:
            match_json_str = re.search(
                r'(\{\\"common\\":.*?)]\\n"]\)</script><div hidden', html_str
            )
        json_str = match_json_str.group(1)
        cleaned_string = json_str.replace("\\", "").replace(r"u0026", r"&")
        room_store = re.search(
            '"roomStore":(.*?),"linkmicStore"', cleaned_string, re.S
        ).group(1)
        anchor_name = re.search(
            '"nickname":"(.*?)","avatar_thumb', room_store, re.S
        ).group(1)
        room_store = room_store.split(',"has_commerce_goods"')[0] + "}}}"
        json_data = json.loads(room_store)["roomInfo"]["room"]
        json_data["anchor_name"] = anchor_name
        return json_data

    except Exception as e:
        print(f"Failure address：{url} Prepare to switch parsing methods {e}")
        web_rid = re.match(r"https://live.douyin.com/(\d+)", url).group(1)
        headers["Cookie"] = "sessionid=73d300f837f261eaa8ffc69d50162700"
        url2 = f"https://live.douyin.com/webcast/room/web/enter/?aid=6383&app_name=douyin_web&live_id=1&web_rid={web_rid}"
        req = urllib.request.Request(url2, headers=headers)
        response = opener.open(req, timeout=15)
        json_str = response.read().decode("utf-8")
        json_data = json.loads(json_str)["data"]
        room_data = json_data["data"][0]
        room_data["anchor_name"] = json_data["user"]["nickname"]
        return room_data


def get_douyin_stream_url(json_data: dict) -> dict:
    anchor_name = json_data.get("anchor_name", None)

    result = {
        "anchor_name": anchor_name,
        "is_live": False,
    }

    status = json_data.get("status", 4)  # 直播状态 2 是正在直播、4 是未开播

    if status == 2:
        stream_url = json_data["stream_url"]
        flv_url_list = stream_url["flv_pull_url"]
        m3u8_url_list = stream_url["hls_pull_url_map"]
        quality_list: list = list(m3u8_url_list.keys())
        while len(quality_list) < 4:
            quality_list.append(quality_list[-1])
        # video_qualities = {"原画": 0, "蓝光": 0, "超清": 1, "高清": 2, "标清": 3}
        # quality_index = video_qualities.get(video_quality)
        quality_index = 0
        quality_key = quality_list[quality_index]
        m3u8_url = m3u8_url_list.get(quality_key)
        flv_url = flv_url_list.get(quality_key)

        result["m3u8_url"] = m3u8_url
        result["flv_url"] = flv_url
        result["is_live"] = True
        result["record_url"] = m3u8_url
    return result


def get_cookies():
    url = "https://live.douyin.com/745964462470"
    driver = Driver(browser="chrome", headless=True)
    driver.open(url)
    cookies = driver.get_cookies()
    cookie_str = "; ".join(
        [f"{cookie['name']}={cookie['value']}" for cookie in cookies]
    )
    driver.quit()
    return cookie_str


def get_xbogus(url) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/14.2 Chrome/87.0.4280.141 Mobile Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Cookie": "s_v_web_id=verify_lk07kv74_QZYCUApD_xhiB_405x_Ax51_GYO9bUIyZQVf",
    }
    query = urllib.parse.urlparse(url).query
    xbogus = execjs.compile(open("./x-bogus.js").read()).call(
        "sign", query, headers["User-Agent"]
    )
    return xbogus


def get_sec_user_id(url):
    response = opener.open(url, timeout=15)
    redirect_url = response.url
    sec_user_id = re.search(r"sec_user_id=([\w\d_\-]+)&", redirect_url).group(1)
    room_id = redirect_url.split("?")[0].rsplit("/", maxsplit=1)[1]
    return room_id, sec_user_id


def get_live_room_id(room_id, sec_user_id):
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/14.2 Chrome/87.0.4280.141 Mobile Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
        "Cookie": "s_v_web_id=verify_lk07kv74_QZYCUApD_xhiB_405x_Ax51_GYO9bUIyZQVf",
    }
    url = f"https://webcast.amemv.com/webcast/room/reflow/info/?verifyFp=verify_lk07kv74_QZYCUApD_xhiB_405x_Ax51_GYO9bUIyZQVf&type_id=0&live_id=1&room_id={room_id}&sec_user_id={sec_user_id}&app_id=1128&msToken=wrqzbEaTlsxt52-vxyZo_mIoL0RjNi1ZdDe7gzEGMUTVh_HvmbLLkQrA_1HKVOa2C6gkxb6IiY6TY2z8enAkPEwGq--gM-me3Yudck2ailla5Q4osnYIHxd9dI4WtQ=="
    xbogus = get_xbogus(url)
    url = url + "&X-Bogus=" + xbogus
    req = urllib.request.Request(url, headers=headers)
    response = opener.open(req, timeout=15)
    html_str = response.read().decode("utf-8")
    json_data = json.loads(html_str)
    web_rid = json_data["data"]["room"]["owner"]["web_rid"]
    return web_rid


def get_live_url(url: str) -> str:
    room_id, sec_user_id = get_sec_user_id(url)
    web_rid = get_live_room_id(room_id, sec_user_id)
    # print(web_rid)
    return web_rid


def get_info(text: str):
    # Regular expression to match a URL
    url_pattern = r"https?://[^\s]+"
    # Find all URLs in the text
    urls = re.findall(url_pattern, text)
    # Extract the first URL, if any
    url = urls[0] if urls else None
    live_url = "https://live.douyin.com/" + get_live_url(url)
    json_data = get_douyin_stream_data(live_url)
    port_info = get_douyin_stream_url(json_data)
    return port_info
    # print(port_info)
    # if port_info['is_live']:
    #     real_url = port_info['record_url']
    # print(real_url)


app = Flask(__name__)
CORS(app)


@app.route("/")
def hello():
    return jsonify({"message": "Hello!"})


@app.route("/info")
def info():
    url = request.args.get("url")
    if url == None:
        abort(400)
    else:
        try:
            info = get_info(url)
            return jsonify(data=info, code=http.HTTPStatus.OK.value, message="success")
        except Exception as e:
            print(e)
            abort(500)


if __name__ == "__main__":
    app.config["JSON_AS_ASCII"] = False
    app.run(host="0.0.0.0", port=3003)


# record_url= 'https://live.douyin.com/528253159735'
# record_url= 'https://live.douyin.com/438378054542'
# json_data = get_douyin_stream_data(record_url)
# port_info = get_douyin_stream_url(json_data, "原画")
# print(port_info)
# if port_info['is_live']:
#     real_url = port_info['record_url']
#     print(real_url)
