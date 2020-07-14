from pyppeteer import launch
from config import config
import asyncio
import random
base_config = config['base_config']


class Slider:
    def __init__(self, url, cookie):
        self.url = url
        self.cookie = cookie

    @staticmethod
    async def _create_browser():
        browser = await launch({
            'executablePath': base_config.CHROME_PATH,
            'ignoreHTTPSErrors': True,  # 是否忽略HTTPS错误
            'headless': False,  # 打开/关闭无头模式
            'autoClose': False,  # 程序结束是否自动关闭浏览器
            # Chrome启动参数
            'args': [
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-gpu',
                'blink-settings=imagesEnabled=false',
                '--mute-audio',
                '--no-sandbox',
                '--hide-scrollbars',
                '--disable-images',
                '--disable-extensions',
                '--disable-bundled-ppapi-flash',
                '--disable-setuid-sandbox',
                '--window-size=1920,1080',
            ]
        })
        return browser

    async def slider_verify(self):
        browser = await self._create_browser()
        page = (await browser.pages())[0]
        await page.goto(self.url)
        await page.evaluate(
            '''() =>{ Object.defineProperties(navigator,{ webdriver:{ get: () => false } }) }''')
        await asyncio.sleep(2)
        await self._slider_verify(page)

    async def _slider_verify(self, page):
        btn_position = await page.evaluate('''
               () =>{
                return {
                 x: document.querySelector('#nc_1_n1z').getBoundingClientRect().x,
                 y: document.querySelector('#nc_1_n1z').getBoundingClientRect().y,
                 width: document.querySelector('#nc_1_n1z').getBoundingClientRect().width,
                 height: document.querySelector('#nc_1_n1z').getBoundingClientRect().height
                 }}
                ''')
        track = Slider.get_track(300)
        await self.slide_move(track, page, btn_position)

    @staticmethod
    def get_track(offset):
        """
        模拟人移动滑块验证码的轨迹
        :param offset: 偏移量-->int
        :return: 滑动轨迹-->list
        """
        track = []
        # 滑块的起始位置
        distance = 5
        # 设定变速临界值
        border = int(offset * 4 / 5)
        # 设置间隔时间
        t = 0.2
        # 设置初始速度
        offset += 4
        v = 0
        while distance < offset:
            # 根据是否到临界点改变运动状态
            if distance < border:
                # 设置加速度
                a = 5
            else:
                # 设置减速度
                a = -0.5
            v0 = v
            v = v0 + a * t
            move = v0 * t + 0.5 * a * t * t
            distance += move
            track.append(round(move))

        return track

    async def slide_move(self, track, page, position):
        """
        用鼠标模拟人拖动滑块
        :param track:滑动轨迹-->list
        :return:
        """
        # 获取拖动按钮
        back_tracks = [-2, -1, -2, -2]
        x = position['x'] + position['width'] / 2
        y = position['y'] + position['height'] / 2
        await page.mouse.move(x, y)
        await page.mouse.down()
        for i in track:
            x += i
            await page.mouse.move(x, y)
            await asyncio.sleep(random.random() / 1000)
        await asyncio.sleep(random.random())
        for j in back_tracks:
            x += j
            await page.mouse.move(x, y)
            await asyncio.sleep(random.random() / 1000)
        await asyncio.sleep(random.random())
        await page.mouse.up()
        await asyncio.sleep(2)


