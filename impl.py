import re
import json
import time
import logging
from srun_encryptions import *

try:
    from urllib import urlencode, unquote, request
    from urlparse import urlparse, parse_qsl, ParseResult
except ImportError:
    # Python 3 fallback
    from urllib.parse import (
        urlencode, unquote, urlparse, parse_qsl, ParseResult
    )
    from urllib import request

# constants and api
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 '
                  'Safari/537.36 '
}
PORTAL_BASE_URL = ''
logger = logging.getLogger(__name__)


def set_portal_base_url(url: str):
    global PORTAL_BASE_URL
    PORTAL_BASE_URL = url


def http_add_params_to_url(url: str, params: dict) -> str:
    url: str = unquote(url)
    parsed_url: ParseResult = urlparse(url)
    # add new params
    GET_params_flatten: str = parsed_url.query
    GET_params: dict = dict(parse_qsl(GET_params_flatten))
    GET_params.update(params)

    # Bool and Dict values were overwritten to json-friendly values
    GET_params.update({
        k: json.dumps(v)
        for k, v in GET_params.items()
        if isinstance(v, (bool, dict))
    })

    GET_params_flatten: str = urlencode(GET_params, doseq=True)
    url: str = ParseResult(
        parsed_url.scheme, parsed_url.netloc, parsed_url.path,
        parsed_url.params, GET_params_flatten, parsed_url.fragment
    ).geturl()
    return url


def http_get(url: str, params: dict = None, headers: dict = None) -> str:
    '''
    Wrapped HTTP GET.
    Don't use `requests` library because sometimes this repo runs without network connection.
    So installing `requests` may not be handy all the time.
    :see: https://stackoverflow.com/questions/2506379/add-params-to-given-url-in-python
    '''

    if params is None:
        params = {}
    else:
        url: str = http_add_params_to_url(url, params)

    if headers is None:
        headers = {}

    req = request.Request(url, headers=headers)
    resp = request.urlopen(req)
    text = resp.read().decode('utf-8')
    return text


def http_post(url: str, params: dict = None, data: dict = None, headers: dict = None) -> str:
    '''
    Wrapped HTTP POST.
    Don't use `requests` library because sometimes this repo runs without network connection.
    So installing `requests` may not be handy all the time.
    :see: https://blog.csdn.net/Asura_____/article/details/123320731
    '''
    if params is None:
        params = {}
    else:
        url: str = http_add_params_to_url(url, params)

    if headers is None:
        headers = {}

    if data is None:
        data = {}
        encoded_data = ''
    else:
        encoded_data = urlencode(data).encode('utf-8')

    req = request.Request(url=url, data=encoded_data, headers=headers)
    resp = request.urlopen(req)
    text = resp.read().decode('utf-8')

    return text


def request_ip() -> str:
    '''
    Get IP address of this machine, will be used in later login.
    '''
    global PORTAL_BASE_URL, HEADERS
    url = f'{PORTAL_BASE_URL}/'
    text = http_get(url, headers=HEADERS)
    # a HTML document
    config: str = re.search(r'var CONFIG = ({.*})', text, flags=re.S).group(1)
    ip: str = re.search(r'ip.*?:.*?"(.*?)"', config).group(1)
    return ip


def request_token(username: str, ip: str) -> str:
    '''
    Get token for a session.
    '''
    global PORTAL_BASE_URL, HEADERS

    time_nounce: int = int(time.time() * 1000)
    url = f'{PORTAL_BASE_URL}/cgi-bin/get_challenge'
    params = {
        "callback": f'jQuery112406382209524580216_{time_nounce}',
        "username": username,
        "ip": ip,
        "_": time_nounce
    }
    text = http_get(url, params=params, headers=HEADERS)

    # a HTML document, jsonp, don't include brackets
    text: str = text[text.index('(') + 1: -1]
    j = json.loads(text)

    token = j['challenge']
    return token


def build_login_params(username: str, password: str, ip: str, token: str) -> dict:
    # constant params
    constants = {
        'acid': '1',
        'enc_ver': 'srun_bx1',
        'n': '200',
        'type': '1'
    }

    # payload['info']
    info: dict = {
        "username": username,
        "password": password,
        "ip": ip,
        "acid": constants['acid'],
        "enc_ver": constants['enc_ver']
    }
    flatten_info: str = str(info)
    flatten_info: str = re.sub("'", '"', flatten_info)
    flatten_info: str = re.sub(" ", '', flatten_info)

    encoded_info_prefixed: str = r'{SRBX1}' + get_base64(get_xencode(flatten_info, token))

    # md5 will be used later
    # payload['chksum']
    password_md5: str = get_md5(password, token)
    # it's wierd, but it works
    chksum_segments = [
        token, username,
        token, password_md5,
        token, constants['acid'],
        token, ip,
        token, constants['n'],
        token, constants['type'],
        token, encoded_info_prefixed
    ]
    chksum: str = get_sha1(''.join(chksum_segments))

    # final params
    time_nounce: int = int(time.time() * 1000)
    res = {
        'callback': f'jQuery11240645308969735664_{time_nounce}',
        'action': 'login',
        'username': username,
        'password': r'{MD5}' + password_md5,
        'ac_id': constants['acid'],
        'ip': ip,
        'chksum': chksum,
        'info': encoded_info_prefixed,
        'n': constants['n'],
        'type': constants['type'],
        'os': 'Windows 10',
        'name': 'Windows',
        'double_stack': '0',
        '_': time_nounce
    }
    return res


def request_login(params: dict) -> dict:
    global PORTAL_BASE_URL, HEADERS
    url = f'{PORTAL_BASE_URL}/cgi-bin/srun_portal'

    # a HTML document, jsonp
    text: str = http_get(url, params=params, headers=HEADERS)
    # don't include brackets
    text: str = text[text.index('(') + 1: -1]
    j = json.loads(text)

    return j


def login(username: str, password: str):
    global PORTAL_BASE_URL, HEADERS

    ip = request_ip()
    logger.info(f'ip is {ip}')

    token = request_token(username, ip)
    logger.info(f'token is {token}')

    params = build_login_params(username, password, ip, token)
    j = request_login(params)

    if j['ecode'] == 0:
        logger.info('login requested.')
        if j['suc_msg'] == 'login_ok':
            logger.info('login success!')
            logger.debug(f'online ip is {j["online_ip"]}, '
                         f'username is {j["username"]}, '
                         f'real name is {j["real_name"]}')
        elif j['suc_msg'] == 'ip_already_online_error':
            logger.error('login failed.')
            logger.error('server reported this ip is already online, cannot login twice.')
        else:
            logger.error('login failed, unknown error, response json as follows:')
            logger.error(json.dumps(j, ensure_ascii=False, indent=4))
    else:
        logger.error('server denied login request, response json as follows:')
        logger.error(json.dumps(j, ensure_ascii=False, indent=4))


def request_client_id(username: str) -> str:
    '''
    todo
    Client id is used to logout from server.
    It was implemented by checking your ip in a list of all devices.
    '''
    global PORTAL_BASE_URL, HEADERS

    this_ip = request_ip()

    url = f'{PORTAL_BASE_URL}/v1/auth/device/get'
    params = {'user_name': username}
    text = http_get(url, params=params, headers=HEADERS)

    return text


def request_logout(username: str):
    '''todo'''
    global PORTAL_BASE_URL, HEADERS
    url = f'{PORTAL_BASE_URL}/v1/auth/online_device/drop'
    data = {
        'user_name': username,
        'drop_type': 'radius',
    }

    # need to modify headers here
    headers = dict(**HEADERS)
    headers['User-Auth'] = username

    text = http_post(url, data=data, headers=headers)
    j = json.loads(text)

    if j['code'] == 0:
        logger.info('logout successfully.')
    else:
        logger.error('logout failed, server replied:')
        logger.error(json.dumps(j, indent=4, ensure_ascii=False))


def logout(username: str):
    '''todo'''
    raise NotImplementedError
    # client_id :str = request_client_id(username)
    # request_logout(username)
