import requests
import pandas as pd
from lxml import etree
from config import config

youku_config = config['youku_config']


class YoukuSpider(object):
    url = 'https://user.youku.com/page/usc/index/?spm=a2hcb.12675304.uerCenter.5!2~5~5!2~5~A'

    def __init__(self, cookies):
        self.headers = {
            'Referer': 'https://www.youku.com/?spm=a2hcb.playlsit.header-contain.5~5~5~A'
        }
        self.data_field = {
            "标题": [],
            "观看进度时间": [],
            "观看进度率": [],
            "观看日期时间": [],
            "封面图片": [],
        }
        self.session = requests.Session()
        self.session.cookies = self._serialization_cookies(cookies)

    def _serialization_cookies(self, cookies):
        cookie_list = cookies.replace(' ', '').split(';')
        cookie_dict = {}
        for c in cookie_list:
            key, value = c.split('=')
            cookie_dict[key] = value
        return requests.utils.cookiejar_from_dict(cookie_dict)

    def run(self):
        response = self.session.get(self.url, headers=self.headers)
        self.parse_youku(response)

    def parse_youku(self, response):
        html = etree.HTML(response.text)
        divs = html.xpath("//div[@class='categorypack_yk_pack pack_cover_icon']")
        for div in divs:
            img = div.xpath('./div[@class="categorypack_pack_cover"]//a//img/@src')[0]  # 图片
            progress_time = \
                div.xpath('./div[@class="categorypack_pack_cover"]//span[@class="categorypack_p_rb"]//text()')[
                    0]  # 观看进度时间
            title = div.xpath("./div[@class='categorypack_info_list']//a/text()")[0]  # 标题
            try:
                watch_data = \
                    div.xpath(
                        "./div[@class='categorypack_info_list']/div[@class='categorypack_subtitle ']/span/text()")[0]
                progress_rate = watch_data.split('  ')[0]  # 观看进度
                watch_time = watch_data.split('  ')[1]  # 观看日期时间
                self.data_field["观看进度率"].append(progress_rate)
                self.data_field["观看日期时间"].append(watch_time)
            except IndexError:
                self.data_field["观看进度率"].append('暂无数据，该网站无可播源')
                self.data_field["观看日期时间"].append('暂无数据，该网站无可播源')
            self.data_field["标题"].append(title)
            self.data_field["观看进度时间"].append(progress_time)
            self.data_field["封面图片"].append(img)
        data_frame = pd.DataFrame(self.data_field)
        data_frame.to_csv(youku_config.YOUKU_FILE_PATH)


if __name__ == '__main__':
    scheduler = YoukuSpider(youku_config.YOUKU_COOKIES)
    scheduler.run()
