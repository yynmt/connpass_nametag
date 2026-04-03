# ################################################################
# connpass API
# API リファレンス: https://connpass.com/about/api/v2/
# ################################################################
import os
import time
import requests

# API キーファイル名
API_KEY_FILE = 'api_key'
# API キーファイルパス
API_KEY_PATH = os.path.join(os.path.dirname(__file__), API_KEY_FILE)
# API へのリクエスト取得単位
COUNT = 100
# サーバ負荷軽減のための待機時間 (単位: 秒)
SLEEP_TIME = 1


class ConnpassAPI:
    def __init__(self):
        # connpass API の X-API-Key を読み込み
        api_key = ''
        with open(API_KEY_PATH, mode='r') as f:
            api_key = f.read()

        # https リクエスト用のヘッダー
        self.__headers = {
            'User-Agent': 'curl',
            'X-API-Key': api_key,
        }

    def search_event(self):
        """イベント検索
        Request URL: https://connpass.com/api/v2/events/?keyword=hoge
        名札生成には不要なため未実装
        """
        pass

    def get_user(self, user_list: list[str]) -> list[dict]:
        """ユーザ情報取得
        Request URL: https://connpass.com/api/v2/users/?nickname=nickname1,nickname2

        Args:
            user_list (list[str]): connpass ユーザ ID のリスト
        Returns:
            list[dict]: API が返却した dict
        """
        res = []

        # API を COUNT 件ずつ叩く
        for i in range(0, len(user_list), COUNT):
            tmp_user_list = user_list[i: i + COUNT]
            url = 'https://connpass.com/api/v2/users/'
            params = {
                'nickname': ','.join(tmp_user_list),
                'count': str(COUNT),
            }

            res_json = {}
            try:
                response = requests.get(url, headers=self.__headers, params=params)
                response.raise_for_status()

                res_json = response.json()
                res.extend(res_json.get('users', []))
            except requests.exceptions.RequestException as e:
                print(e)

            if len(tmp_user_list) != res_json.get('results_returned', 0):
                # API に問い合わせたユーザ数と返されたユーザ数が一致しない
                print(f'len(tmp_user_list): {len(tmp_user_list)}')
                print(f'res_json["results_returned"]: {res_json["results_returned"]}')

            # API リクエスト制限のため待機
            time.sleep(SLEEP_TIME)

        return res

    def get_user_group(self):
        """ユーザ所属グループ取得
        Request URL: https://connpass.com/api/v2/users/{nickname}/groups/
        名札生成には不要なため未実装
        """
        pass

    def get_user_attended_event(self):
        """ユーザ参加イベント取得
        Request URL: https://connpass.com/api/v2/users/{nickname}/attended_events/
        名札生成には不要なため未実装
        """
        pass
