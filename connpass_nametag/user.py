import os
import time
import requests
from pathlib import Path

ICON_DIR_PATH = str(Path(__name__).parent / 'icon')
Path(ICON_DIR_PATH).mkdir(exist_ok=True)


class User:
    CATEGORY = {
        'STAFF': (195, 13, 35),
        'PRESS': (0, 160, 233),
        'SPONSOR': (96, 25, 134),
    }
    DEFAULT_CATEGORY_TEXT = ''
    DEFAULT_CATEGORY_COLOR = (208, 208, 208)

    def __init__(self, connpass_id: str):
        self.user_name = connpass_id
        self.twitter_id = ''
        self.display_name = ''
        self.rcpt_number = -1
        self.category = ''
        self.icon_url = ''
        self.icon_path = ''
        self.twitter_id = ''

    def download_icon(self, over_write=False, skip=False) -> None:
        # アイコンがすでにダウンロード済み
        if self.icon_path:
            return

        # ダウンロード済みのアイコンを探索
        glob_p = f'{self.user_name}.*'
        gr = list(Path(ICON_DIR_PATH).glob(glob_p))
        if gr:
            self.icon_path = str(gr[0])
            print(f'Already download icon: {self.icon_path}')
            # 上書きを許可していない場合
            if not over_write:
                print('Skip download')
                return

        # デバッグ目的でこれ以降の処理をスキップ
        if skip:
            return

        # サーバー負荷軽減のため1秒待機
        time.sleep(1)

        # アイコンのURLがConnpassで見つかった
        if self.icon_url:
            # Connpassのアイコンをダウンロード
            response = requests.get(self.icon_url)
            icon_img = response.content
            _, ext = os.path.splitext(self.icon_url)
            self.icon_path = str(Path(ICON_DIR_PATH) / f'{self.user_name}-{self.rcpt_number}{ext}')
            print(f'Download icon: {self.icon_url} -> {self.icon_path}')
            with open(self.icon_path, "wb") as f:
                f.write(icon_img)

    def get_connpass_icon_url(self, connpass_dict_list: list[dict]) -> None:
        self.icon_url = ''

        for c_dict in connpass_dict_list:
            if c_dict['nickname'] == self.user_name:
                if c_dict['image_url']:
                    self.icon_url = c_dict['image_url']
                break
