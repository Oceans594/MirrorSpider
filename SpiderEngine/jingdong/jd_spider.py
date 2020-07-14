import requests
import re
import json
from config import config
from lxml import etree
import pandas as pd

jd_config = config['jd_config']


class JDSpider(object):
    action_url = "https://order.jd.com/center/list.action"
    action_params = [3, 2014, 2015, 2016, 2017, 2018, 2019, 2020]
    order_url = "https://order.jd.com/lazy/getOrderProductInfo.action"

    def __init__(self, cookies):
        self.sesson = requests.Session()
        self.sesson.cookies = self._serialization_cookies(cookies)
        self.data_field = {
            "年份": [],
            "ID": [],
            "卖家": [],
            "名称": [],
            "价格": []
        }

    def _serialization_cookies(self, cookie):
        cookies_dict = {}
        cookies_list = cookie.split(';')
        for cookie in cookies_list:
            key, value = cookie.split("=")
            cookies_dict[key] = value
        return requests.utils.cookiejar_from_dict(cookies_dict)

    def _save_orders(self):
        data_frame = pd.DataFrame(self.data_field)
        data_frame.to_csv(jd_config.JD_ORDER_FILE_PATH)

    def get_order_requests_params(self):
        for params_d in self.action_params:
            url = self.action_url + f"?search=0&d={params_d}&s=4096"
            response = self.sesson.get(url)
            ele = etree.HTML(response.content.decode('gbk'))
            obj_list = ele.xpath('//table[@class="td-void order-tb"]/tbody')[1:]
            print(response.status_code, response.url)
            try:
                data = {
                    'orderWareIds': '{}'.format(
                        re.findall(r"ORDER_CONFIG\['orderWareIds'\]='([\d,]+)'", response.content.decode('GBK'))[0]),
                    'orderWareTypes': '{}'.format(
                        re.findall(r"ORDER_CONFIG\['orderWareTypes'\]='([\d,]+)'", response.content.decode('GBK'))[0]),
                    'orderIds': '{}'.format(
                        re.findall(r"ORDER_CONFIG\['orderIds'\]='([\d,]+)'", response.content.decode('GBK'))[0]),
                    'orderTypes': '{}'.format(
                        re.findall(r"ORDER_CONFIG\['orderTypes'\]='([\d,]+)'", response.content.decode('GBK'))[0]),
                    'orderSiteIds': '{}'.format(
                        re.findall(r"ORDER_CONFIG\['orderSiteIds'\]='([\d,]+)'", response.content.decode('GBK'))[0]),
                    'sendPays': '{}'.format(
                        re.findall(r"ORDER_CONFIG\['sendPays'\]='([\d,]+)'", response.content.decode('GBK'))[0]),
                }
            # except IndexError as ierror:
            except Exception as e:
                print(e)
                yield {}, obj_list, params_d
            else:
                yield data, obj_list, params_d

    def get_order_info(self):
        for params, obj_list, year in self.get_order_requests_params():
            if params:
                response = self.sesson.post(self.order_url, data=params)
                data_list = json.loads(response.content.decode('GBK'))
                ret_list = []
                for obj in obj_list:
                    try:
                        item = data_list[obj_list.index(obj)]
                        item['goods-number'] = ''.join(obj.xpath('.//div[@class="goods-number"]//text()')).strip()
                        item['consignee tooltip'] = ''.join(
                            obj.xpath('.//div[@class="consignee tooltip"]/text()')).strip()
                        item['amount'] = ''.join(obj.xpath('.//div[@class="amount"]//text()')).strip()
                        item['order-shop'] = ''.join(obj.xpath('.//span[@class="order-shop"]//text()')).strip()
                        ret_list.append(item)
                    except Exception:
                        continue
                for info in ret_list:
                    self.data_field['年份'].append(year)
                    self.data_field['ID'].append(info.get('productId'))
                    self.data_field['卖家'].append(info.get('order-shop'))
                    self.data_field['名称'].append(info.get('name'))
                    self.data_field['价格'].append(info.get('amount').replace('\n', ''))

        self._save_orders()


if __name__ == '__main__':
    schduler = JDSpider(jd_config.JD_COOKIES)
    schduler.get_order_info()
