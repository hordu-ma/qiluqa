import json
import base64
import os
import ssl
from urllib.error import HTTPError
from urllib.request import Request, urlopen

context = ssl._create_unverified_context()
# 请求接口
REQUEST_URL = "https://gjbsb.market.alicloudapi.com/ocrservice/advanced"


def get_img(img_file):
    """将本地图片转成base64编码的字符串，或者直接返回图片链接"""
    # 简单判断是否为图片链接
    if img_file.startswith("http"):
        return img_file
    else:
        with open(os.path.expanduser(img_file), 'rb') as f:  # 以二进制读取本地图片
            data = f.read()
    try:
        encode_str = str(base64.b64encode(data), 'utf-8')
    except TypeError:
        encode_str = base64.b64encode(data)
    return encode_str


def post_url(headers, body):
    """
    发送请求，获取识别结果
    """
    try:
        params = json.dumps(body).encode(encoding='UTF8')
        req = Request(REQUEST_URL, params, headers)
        r = urlopen(req, context=context)
        html = r.read()
        return html.decode("utf8")
    except HTTPError as e:
        print(e.code)
        print(e.read().decode("utf8"))


def ocr_request(appcode, img_file, params):
    """
    请求接口
    """
    if params is None:
        params = {}
    img = get_img(img_file)
    if img.startswith('http'):  # img 表示图片链接
        params.update({'url': img})
    else:  # img 表示图片base64
        params.update({'img': img})

    # 请求头
    headers = {
        'Authorization': 'APPCODE %s' % appcode,
        'Content-Type': 'application/json; charset=UTF-8'
    }

    response = post_url(headers, params)
    data = json.loads(response)
    texts = data.get('prism_wordsInfo')
    _new_text = ''
    # 返回的数据类型是字符串
    for text in texts:
        _new_text = _new_text.join(text.get('word'))
    return _new_text

