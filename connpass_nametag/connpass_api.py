# connpass API
# API リファレンス
# https://connpass.com/about/api/

import time
import requests

API_KEY_FILE = 'api_key'
COUNT = 100


class ConnpassAPI:
    def __init__(self):
        # connpass APIのX-API-Keyを読み込み
        api_key = ''
        with open(API_KEY_FILE, mode='r') as f:
            api_key = f.read()

        # httpリクエスト用のヘッダー
        self.headers = {
            'User-Agent': 'curl',
            'X-API-Key': api_key,
        }

    def search_event(self):
        """
        イベントサーチAPI
        Request URL:
            https://connpass.com/api/v2/events/?keyword=hoge
        """
        pass

    def get_user(self, user_list: list[str]) -> list[dict]:
        """
        ユーザーAPI
        Request URL:
            https://connpass.com/api/v2/users/?nickname=nickname1,nickname2
        """
        res = []

        # APIをCOUNT件ずつ叩く
        for i in range(0, len(user_list), COUNT):
            tmp_user_list = user_list[i: i + COUNT]
            url = 'https://connpass.com/api/v2/users/'
            params = {
                'nickname': ','.join(tmp_user_list),
                'count': str(COUNT),
            }

            res_json = {}
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                res_json = response.json()
                res.extend(res_json.get('users', []))
            except requests.exceptions.RequestException as e:
                print(e)

            if len(tmp_user_list) != res_json.get('results_returned', 0):
                # APIに問い合わせたユーザ数と返されたユーザ数が一致しない
                print(f'len(tmp_user_list): {len(tmp_user_list)}')
                print(f'res_json["results_returned"]: {res_json["results_returned"]}')

            # APIリクエスト制限のため1秒待機
            time.sleep(1)

        return res

    def get_user_group(self):
        """
        ユーザー所属グループAPI
        Request URL:
            https://connpass.com/api/v2/users/{nickname}/groups/
        """
        pass

    def get_user_attended_event(self):
        """
        ユーザー参加イベントAPI
        Request URL:
            https://connpass.com/api/v2/users/{nickname}/attended_events/
        """
        pass
