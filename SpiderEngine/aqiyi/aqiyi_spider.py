# -*- coding:utf-8 -*-
_author_ = '54462'
import requests
import json
import pandas as pd
from config import config

iqiyi_config = config['iqiyi_config']
class AqiyiSpider(object):
    def __init__(self, num, cookies):
        self.url = f'https://l-rcd.iqiyi.com/apis/qiyirc/getallrc?18WaWcfoAiEXy3AIVYdqIrA3am3T114bR0tlSzLZWCXm2hTIpTkAagWNNum22zfMkqT5m181&ckuid=892569c9e3d02be7cda9663fd4f4e77a&only_long=1&vp=0&pageNum=1&pageSize={num}'
        self.headers = {'host': 'l-rcd.iqiyi.com',
                        'origin': 'https://www.iqiyi.com',
                        'referer': 'https://www.iqiyi.com/u/record?vfrm=pcw_home&vfrmblk=A&vfrmrst=tj_record',
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
                        'cookie': cookies
                    }
        self.data_field = {
            "剧名": [],
            "集名": [],
            "标题": [],
            "总集数": [],
            "封面图片": [],
        }

    def run(self):
        response = requests.get(self.url, headers=self.headers)
        self.parse_json(response)

    def parse_json(self, response):
        json_data = json.loads(response.text)
        records = json_data.get('data').get('records')
        for record in records:
            tv_name = record.get('albumName')  # 电视剧名
            video_name = record.get('videoName')  # 集名
            video_title = record.get('subTitle')  # 标题
            all_set = record.get('allSet')  # 总集数
            video_image = record.get('videoImageUrl')  # 封面图片
            self.data_field["剧名"].append(tv_name)
            self.data_field["集名"].append(video_name)
            self.data_field["标题"].append(video_title)
            self.data_field["总集数"].append(all_set)
            self.data_field["封面图片"].append(video_image)
        data_frame = pd.DataFrame(self.data_field)
        data_frame.to_csv(iqiyi_config.IQIYI_FILE_PATH)


if __name__ == '__main__':
    A = AqiyiSpider(1000, iqiyi_config.IQIYI_COOKIES)
    A.run()
