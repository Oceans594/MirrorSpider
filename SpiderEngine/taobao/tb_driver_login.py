from pyppeteer import launch
from config import config
import asyncio
import random
from retry import retry
import json

tb_config = config['tb_config']
base_config = config['base_config']


class TBLogin(object):
    login_url = "https://login.taobao.com/member/login.jhtml"

    @staticmethod
    async def _create_browser():
        browser = await launch({
            'executablePath': base_config.CHROME_PATH,
            'ignoreHTTPSErrors': True,  # 是否忽略HTTPS错误
            'headless': True,  # 打开/关闭无头模式
            'autoClose': False,  # 程序结束是否自动关闭浏览器
            'devtools': True,
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

    async def login(self):
        browser = await self._create_browser()
        page = (await browser.pages())[0]
        await page.setViewport({'width': 1920, 'height': 1080})
        await page.evaluate(
            '''() =>{ Object.defineProperties(navigator,{ webdriver:{ get: () => false } }) }''')
        await page.setUserAgent(
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36')
        await page.goto(self.login_url)
        await page.type(
            "#fm-login-id", tb_config.TB_USERNAME, {'delay': random.randint(200, 300) - 50}
        )
        await page.type(
            "#fm-login-password", tb_config.TB_PASSWORD, {'delay': random.randint(100, 200) - 50}
        )
        # 判断是否出现滑块
        slider = await page.querySelector('#nc_1__scale_text > span')
        if slider:
            await self._slider_verify(page)
        else:
            await asyncio.gather(
                page.waitForNavigation({'waitUntil': 'networkidle2'}),
                page.click("#login-form > div.fm-btn > button")
            )
        await asyncio.gather(
            page.waitForNavigation({'waitUntil': 'networkidle2'}),
            page.click('#bought')
        )
        cookie = await self._get_cookie(page)
        # await browser.close()
        return cookie

    async def _get_cookie(self, page):
        cookies = await page.cookies()
        cookies_dict = {}
        for item in cookies:
            cookies_dict[item.get('name')] = item.get('value')
        with open(tb_config.COOKIES_FILE_PATH, 'w+', encoding='utf-8') as file:
            json.dump(cookies_dict, file)
            print('保存cookies文件成功！')

    @retry(tries=3)
    async def _slider_verify(self, page, distance=308):
        # distance1 = distance - 10
        # distance2 = 10
        btn_position = await page.evaluate('''
               () =>{
                return {
                 x: document.querySelector('#nc_1_n1z').getBoundingClientRect().x,
                 y: document.querySelector('#nc_1_n1z').getBoundingClientRect().y,
                 width: document.querySelector('#nc_1_n1z').getBoundingClientRect().width,
                 height: document.querySelector('#nc_1_n1z').getBoundingClientRect().height
                 }}
                ''')
        x = btn_position['x'] + btn_position['width'] / 2
        y = btn_position['y'] + btn_position['height'] / 2
        await page.mouse.move(x, y)
        await page.mouse.down()
        # await page.mouse.move(x + distance1, y, {'steps': 50})
        # await page.waitFor(800)
        # await page.mouse.move(x + distance1 + distance2, y, {'steps': 30})
        await page.mouse.move(x, y, {'steps': 50})
        await page.waitFor(800)
        await page.mouse.up()
        await asyncio.sleep(0.5)
        verify = await page.querySelector("#nc_1__scale_text > span > b")
        if verify is not None:
            if await (await verify.getProperty('textContent')).jsonValue() == "验证通过":
                print("登陆成功")
                await asyncio.gather(
                    page.click("#login-form > div.fm-btn > button"),
                    page.waitForNavigation({'waitUntil': 'networkidle2'})
                )
            else:
                print("验证失败")
                await page.evaluate("javascript:noCaptcha.reset(1)")
                await asyncio.sleep(random.randint(1, 3))
                raise
        else:
            print("登陆成功")
            await asyncio.gather(
                page.click("#login-form > div.fm-btn > button"),
                page.waitForNavigation({'waitUntil': 'networkidle2'})
            )


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    scheduler = TBLogin()
    loop.run_until_complete(scheduler.login())
