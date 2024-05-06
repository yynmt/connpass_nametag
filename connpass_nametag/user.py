import os
import re
import time
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

ICON_DIR_PATH = str(Path(__name__).parent / 'icon')
Path(ICON_DIR_PATH).mkdir(exist_ok=True)
DRIVER_PATH = str(Path(__name__).parent / 'chromedriver' / 'chromedriver.exe')


class User:
    CATEGORY = {
        'STAFF': (195, 13, 35),
        'PRESS': (0, 160, 233),
        'SPONSOR': (96, 25, 134),
    }
    DEFAULT_CATEGORY_TEXT = ''
    DEFAULT_CATEGORY_COLOR = (208, 208, 208)

    def __init__(self, connpas_id):
        self.user_name = connpas_id
        self.twitter_id = ''
        self.display_name = ''
        self.rcpt_number = -1

        self.category = ''

        self.icon_url = ''
        self.icon_path = ''

        self.twitter_id = ''

    def download_icon(self, over_write=False, skip=False):
        # アイコンがすでにダウンロード済み
        if self.icon_path:
            return

        # ダウンロード済みのアイコンを探索
        glob_p = r'{}.*'.format(self.user_name)
        gr = list(Path(ICON_DIR_PATH).glob(glob_p))
        if gr:
            self.icon_path = str(gr[0])
            print('Already download icon: {}'.format(self.icon_path))
            # 上書きを許可していない場合
            if not over_write:
                print('Skip download ')
                return

        # デバッグ目的でこれ以降の処理をスキップ
        if skip:
            return

        # サーバー負荷軽減のため1秒待機
        time.sleep(0)

        # Connpassからアイコン画像のURLを取得
        self._get_connpass_icon_url()

        # アイコンのURLがConnpassで見つかった
        if self.icon_url:
            # Connpassのアイコンをダウンロード
            response = requests.get(self.icon_url)
            icon_img = response.content
            _, ext = os.path.splitext(self.icon_url)
            self.icon_path = str(Path(ICON_DIR_PATH) / '{}{}'.format(self.user_name, ext))
            print('Download icon: {} -> {}'.format(self.icon_url, self.icon_path))
            with open(self.icon_path, "wb") as f:
                f.write(icon_img)

            # 解像度が48x48より大きい場合このまま終了
            # icon_img = Image.open(self.icon_path).convert('RGBA')
            # if icon_img.size[0] >= 48 and icon_img.size[1] >= 48:
            #     return

        # TwitterのアイコンURLを取得
        # self._get_twitter_icon_url()

        # アイコンのURLがTwitterで見つかった
        # if self.icon_url:
        #     # Twitterのアイコンをダウンロード
        #     response = requests.get(self.icon_url)
        #     icon_img = response.content
        #     _, ext = os.path.splitext(self.icon_url)
        #     self.icon_path = str(Path(ICON_DIR_PATH) / '{}{}'.format(self.user_name, ext))
        #     with open(self.icon_path, "wb") as f:
        #         f.write(icon_img)

    def _get_connpass_icon_url(self):
        self.icon_url = ''
        base_url = r'https://connpass.com/user/'
        profile_url = base_url + self.user_name
        headers = {
            'User-Agent': 'Mozilla/5.0'
        }
        html_text = ''

        try:
            res = requests.get(url=profile_url, headers=headers)
            # レスポンスコードに応じて例外発生
            # res.raise_for_status()
            html_text = res.text
        except requests.exceptions.HTTPError:
            print('HTTP response error')

        try:
            soup = BeautifulSoup(html_text, 'html.parser')
            # 以下に該当する箇所を探索
            # <div id="side_area">
            #   <div class="avatar mb_20 text_center">
            #     <img src="https://media.connpass.com/thumbs/c2/5c/c25c0d282b910de19573c6042175208d.png" width="180" height="180" title="◤◢◤◢◤◢◤◢" alt="◤◢◤◢◤◢◤◢">
            #   </div>
            img_el = soup.find('div', id='side_area').find('div', class_='avatar mb_20 text_center').find('img')
            att = img_el.get('src', '')

            if 'user_no_image' not in att:
                print('Found icon: {}'.format(att))
                self.icon_url = att
            else:
                print('Not found icon')

        except AttributeError as e:
            print('Failed to scraping')
            print(e)

    def _get_twitter_icon_url(self):
        self.icon_url = ''
        base_url = r'https://connpass.com/user/'

        html_text = requests.get(base_url + self.user_name).text
        soup = BeautifulSoup(html_text, 'html.parser')

        # 以下に該当する箇所を探索
        # <a href="http://twitter.com/yynmt_" target="_blank" title="Twitterを見る">
        # <img src="https://connpass.com/static/img/common/icon_twitter.png" alt="Twitterを見る">
        # </a>
        p = r'^.+twitter\.com/(?P<id>.+)$'

        els = soup.find_all('a', attrs={'target': '_blank', 'title': 'Twitterを見る'})
        for el in els:
            att = el.get('href', '')
            m = re.match(p, att)
            if m:
                self.twitter_id = m.group('id')
                break

        # Twitterが未連携
        if self.twitter_id == '':
            return

        twitter_url = 'https://twitter.com/{}/Photo'.format(self.twitter_id)

        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(DRIVER_PATH, options=options)
        driver.get(twitter_url)

        html_text = driver.page_source.encode('utf-8')
        soup = BeautifulSoup(html_text, 'html.parser')
        # 以下に該当する箇所を探索
        # <img alt="画像" draggable="true" src="https://pbs.twimg.com/profile_images/1606715784612679680/1IFEdkzS_400x400.png" class="css-9pa8cd">
        els = soup.find_all('img', attrs={'alt': '画像', 'draggable': 'true'})
        for el in els:
            att = el.get('src', '')
            self.icon_url = att
