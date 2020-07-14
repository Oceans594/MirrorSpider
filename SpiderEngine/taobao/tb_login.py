import requests
from fake_useragent import UserAgent
import re
import json
import os
from config import config
from pyquery import PyQuery as pq

tb_config = config['tb_config']


class TBLogin(object):
    check_url = 'https://login.taobao.com/newlogin/account/check.do?appName=taobao&fromSite=0'  # 检测是否需要验证码的URL
    verify_url = "https://login.taobao.com/newlogin/login.do?appName=taobao&fromSite=0"  # 验证淘宝用户名密码URL
    st_url = 'https://login.taobao.com/member/vst.htm?st={}'  # 访问st码URL
    my_taobao_url = 'http://i.taobao.com/my_taobao.htm'  # 淘宝个人主页

    def __init__(self, username, token, ua, password_crypto, proxy=None):
        self.username = username
        self.token = token
        self.ua = ua
        self.password_crypto = password_crypto
        self.timeout = 3
        self.fake_ua = UserAgent(verify_ssl=False)
        self.session = requests.Session()
        self.proxy = proxy
    @property
    def _verify_password(self):
        """
        验证用户名密码，并获取st码申请URL
        :return: 验证成功返回st码申请地址
        """
        verify_password_headers = {
            'Origin': 'https://login.taobao.com',
            'content-type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://login.taobao.com/member/login.jhtml?spm=a21bo.2017.754894437.1.5af911d9HjW9WC&f=top&redirectURL=https%3A%2F%2Fwww.taobao.com%2F',
        }
        # 验证用户名密码参数
        verify_password_data = {
            'ua': self.ua,
            'loginId': self.username,
            'password2': self.password_crypto,
            'umidToken': self.token,
            'appEntrance': 'taobao_pc',
            'isMobile': 'false',
            'returnUrl': 'https://www.taobao.com/',
            'navPlatform': 'MacIntel',
        }
        try:
            response = self.session.post(self.verify_url, headers=verify_password_headers, data=verify_password_data,
                                         timeout=self.timeout)
            response.raise_for_status()
            # 从返回的页面中提取申请st码地址
        except Exception as e:
            print('验证用户名和密码请求失败，原因：')
            raise e
        # 提取申请st码url
        apply_st_url_match = response.json()['content']['data']['asyncUrls'][0]
        # 存在则返回
        if apply_st_url_match:
            print('验证用户名密码成功，st码申请地址：{}'.format(apply_st_url_match))
            return apply_st_url_match
        else:
            raise RuntimeError('用户名密码验证失败！response：{}'.format(response.text))

    def load_cookies(self):
        # 1、判断cookies序列化文件是否存在
        if not os.path.exists(tb_config.COOKIES_FILE_PATH):
            return False
        # 2、加载cookies
        self.session.cookies = self._deserialization_cookies()
        # 3、判断cookies是否过期
        try:
            referer = self._verify_cookies()
        except Exception as e:
            os.remove(tb_config.COOKIES_FILE_PATH)
            print('cookies过期，删除cookies文件！')
            return False
        print('加载淘宝cookies登录成功!!!')
        return referer

    def _verify_cookies(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        try:
            response = self.session.get(self.my_taobao_url, headers=headers, proxies=self.proxy)
            response.raise_for_status()
            doc = pq(response.text)
            referer = doc('#bought')
            return referer.attr('href')
        except Exception as e:
            print('获取淘宝主页请求失败！原因：')
            raise e

    def _apply_st(self):
        apply_st_url = self._verify_password
        try:
            response = self.session.get(apply_st_url, proxies=self.proxy)
            response.raise_for_status()
        except Exception as e:
            print('申请st码请求失败，原因：')
            raise e
        st_match = re.search(r'"data":{"st":"(.*?)"}', response.text)
        if st_match:
            print('获取st码成功，st码：{}'.format(st_match.group(1)))
            return st_match.group(1)
        else:
            raise RuntimeError('获取st码失败！response：{}'.format(response.text))

    def _serialization_cookies(self):
        cookies_dict = requests.utils.dict_from_cookiejar(self.session.cookies)
        with open(tb_config.COOKIES_FILE_PATH, 'w+', encoding='utf-8') as file:
            json.dump(cookies_dict, file)
            print('保存cookies文件成功！')

    def _deserialization_cookies(self):
        with open(tb_config.COOKIES_FILE_PATH, 'r+', encoding='utf-8') as file:
            cookies_dict = json.load(file)
            cookies = requests.utils.cookiejar_from_dict(cookies_dict)
            return cookies

    def user_check(self):
        """
        检测账号是否需要验证码
        :return:
        """
        data = {
            'loginId': self.username,
            'ua': self.ua,
        }
        try:
            response = self.session.post(self.check_url, data=data, timeout=self.timeout, proxies=self.proxy)
            response.raise_for_status()

        except Exception as e:
            print('检测是否需要验证码请求失败，原因：')
            raise e
        check_resp_data = response.json()['content']['data']
        needcode = False
        # 判断是否需要滑块验证，一般短时间密码错误多次可能出现
        if 'isCheckCodeShowed' in check_resp_data:
            needcode = True
        print('是否需要滑块验证：{}'.format(needcode))
        return needcode

    def _get_umidToken(self):
        """
        获取umidToken参数
        :return:
        """
        response = self.session.get('https://login.taobao.com/member/login.jhtml', proxies=self.proxy)
        st_match = re.search(r'"umidToken":"(.*?)"', response.text)
        print(st_match.group(1))
        return st_match.group(1)

    def login(self):
        if self.load_cookies():
            return True
        self.user_check()
        st = self._apply_st()
        headers = {
            'Host': 'login.taobao.com',
            'Connection': 'Keep-Alive',
            'User-Agent': self.fake_ua.random
        }

        try:
            resp = self.session.get(self.st_url.format(st), headers=headers, proxies=self.proxy)
            resp.raise_for_status()

        except Exception as e:
            print('st码登录请求，原因：')
            raise e
        my_taobao_match = re.search(r'top.location.href = "(.*?)"', resp.text)
        if my_taobao_match:
            print('登录淘宝成功，跳转链接：{}'.format(my_taobao_match.group(1)))
            self.my_taobao_url = my_taobao_match.group(1)
            self._serialization_cookies()
            return True
        else:
            raise RuntimeError('登录失败！response：{}'.format(resp.text))


if __name__ == '__main__':
    scheduler = TBLogin(*tb_config.TB_LOGIN_PARAMS)
    scheduler.login()
