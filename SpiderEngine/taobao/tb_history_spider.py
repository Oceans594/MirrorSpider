import pandas as pd
import json
from config import config
import requests
import asyncio


tb_config = config['tb_config']
loop = asyncio.get_event_loop()


class TBSpider(object):
    order_url = "https://buyertrade.taobao.com/trade/itemlist/asyncBought.htm"
    order_referer = "https://buyertrade.taobao.com/trade/itemlist/list_bought_items.htm"

    def __init__(self, cookies):
        self.sesson = requests.Session()
        self.cookies = cookies
        self.err_list = []
        self.data_field = {
            "ID": [],
            "卖家": [],
            "名称": [],
            "订单创建时间": [],
            "价格": [],
            "状态": [],
            "页码": [],
        }

    def get_history_order(self, pageNum):
        # time.sleep(random.randint(5, 10))
        print(f"爬取第{pageNum}页...")
        params = {
            'action': 'itemlist/BoughtQueryAction',
            'event_submit_do_query': 1,
            '_input_charset': 'utf8'
        }
        form_data = {
            'pageNum': pageNum,
            'pageSize': 15,
            'prePageNo': pageNum - 1
        }
        headers = {
            'origin': 'https://buyertrade.taobao.com',
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
            'cookie': self.cookies
        }
        try:
            resp = self.sesson.post(self.order_url, headers=headers, params=params, data=form_data)
            content = resp.text
            print(content)
        except Exception as e:
            print(e)
        else:
            data = json.loads(content)
            if data.get('mainOrders'):
                self.get_order_info(data.get('mainOrders'), pageNum)
            # elif data.get('url'):
            #     verify = Slider(data.get('url'), self.cookies)
            #     loop.run_until_complete(verify.slider_verify())
                # self.get_history_order(pageNum)
                # if re.search('(.*?)punish', data.get('url')):
                #     print(f"第{pageNum}页爬取失败,原因:需要滑动验证码")
                # self.err_list.append(pageNum)

    def get_order_info(self, order_data, pageNum):
        for order in order_data:
            self.data_field['ID'].append(order.get('id'))
            self.data_field['卖家'].append(order.get('seller').get('shopName'))
            self.data_field['名称'].append(order.get('subOrders')[0].get('itemInfo').get('title'))
            self.data_field['订单创建时间'].append(order.get('orderInfo').get('createTime'))
            self.data_field['价格'].append(order.get('payInfo').get('actualFee'))
            self.data_field['状态'].append(order.get('statusInfo').get('text'))
            self.data_field["页码"].append(pageNum)
        data_frame = pd.DataFrame(self.data_field)
        data_frame.to_csv(tb_config.TB_ORDER_DATA_PATH, mode='a')


if __name__ == '__main__':
    scheduler = TBSpider(tb_config.TB_COOKIES)
    for page in range(1, 60):
        scheduler.get_history_order(page)
    print(scheduler.err_list)
