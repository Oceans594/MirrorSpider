import requests
import time
import random
from urllib import parse
import re
from config import config
import pandas as pd

mongo_config = config['mongo_config']


class MongoSpider(object):
    url = "https://i.mgtv.com/my/record_list?"

    def __init__(self, cookies):
        self.page_count = 0
        self.data_field = {
            "剧名": [],
            "时间进度": [],
            "进度": [],
            "类型": [],
            "封面图片": [],
        }
        self.params = {
            'beforeTime': 0,
            'isFilter': 0,
            'isInteract': 1,
            'callback': f"jQuery182{random.random()}_{int(time.time() * 1000)}".replace('.', ''),
            '_': int(time.time() * 1000)
        }
        self.headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
            'referer': "https://i.mgtv.com/my/watch?lastp=ch_home"
        }
        self.sesson = requests.Session()
        self.sesson.cookies = self._serialization_cookies(cookies)

    def _serialization_cookies(self, cookies):
        cookie_list = cookies.replace(' ', '').split(';')
        cookie_dict = {}
        for c in cookie_list:
            key, value = c.split('=')
            cookie_dict[key] = value
        return requests.utils.cookiejar_from_dict(cookie_dict)

    def get_history(self):
        while True:
            history_url = self.url + parse.urlencode(self.params)
            print(history_url)
            response = self.sesson.get(history_url, headers=self.headers)
            pattern = re.compile(r'[(](.*)[)]', re.S)
            data = (re.findall(pattern, response.text)[0]).replace('null', 'None')
            self.params['callback'] = f"jQuery182{random.random()}_{int(time.time() * 1000)}".replace('.', '')
            self.params['_'] = int(time.time() * 1000)
            self.params['beforeTime'] = eval(data).get('data').get('beforeTime')
            if eval(data).get('data').get('data'):
                self.parse_json(eval(data))
                print(f"第{self.page_count}页成功")
                self.page_count += 1
            else:
                print('爬取结束')
                data_frame = pd.DataFrame(self.data_field)
                data_frame.to_csv(mongo_config.MONGOTV_HISTORY)
                break

    def parse_json(self, data):
        today_records = data.get('data').get('data').get('today')
        week_records = data.get('data').get('data').get('week')
        long_records = data.get('data').get('data').get('long')
        if today_records:
            for today_record in today_records:
                name = today_record.get('vName')  # 剧名
                rate = today_record.get('rate')  # 进度
                video_type = today_record.get('videoType')  # 类型
                time_progress = today_record.get('duration')  # 时间进度
                img = today_record.get('pImage')  # 封面
                self.data_field["剧名"].append(name)
                self.data_field["时间进度"].append(time_progress)
                self.data_field["进度"].append(rate)
                self.data_field["类型"].append(video_type)
                self.data_field["封面图片"].append(img)
        if week_records:
            for week_record in week_records:
                name = week_record.get('vName')  # 剧名
                rate = week_record.get('rate')  # 进度
                video_type = week_record.get('videoType')  # 类型
                time_progress = week_record.get('duration')  # 时间进度
                img = week_record.get('pImage')  # 封面
                self.data_field["剧名"].append(name)
                self.data_field["时间进度"].append(time_progress)
                self.data_field["进度"].append(rate)
                self.data_field["类型"].append(video_type)
                self.data_field["封面图片"].append(img)
        if long_records:
            for long_record in long_records:
                name = long_record.get('vName')  # 剧名
                rate = long_record.get('rate')  # 进度
                video_type = long_record.get('videoType')  # 类型
                time_progress = long_record.get('duration')  # 时间进度
                img = long_record.get('pImage')  # 封面
                self.data_field["剧名"].append(name)
                self.data_field["时间进度"].append(time_progress)
                self.data_field["进度"].append(rate)
                self.data_field["类型"].append(video_type)
                self.data_field["封面图片"].append(img)


if __name__ == '__main__':
    scheduler = MongoSpider(mongo_config.MONGOTV_COOKIES)
    scheduler.get_history()
