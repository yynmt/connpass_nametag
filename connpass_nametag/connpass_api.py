# connpass API
# API リファレンス
# https://connpass.com/about/api/

import json
import paramiko

SSH_HOST = r''
SSH_PORT = 22
SSH_USER = r''
SSH_KEY = r''
SSH_PWD = r''
RECV_SIZE = 1024 * 32
COUNT = 10


class ConnpassAPI:
    def __init__(self):
        # SSHの接続を確立
        self._client = paramiko.SSHClient()
        self._client.load_system_host_keys()
        self._client.set_missing_host_key_policy(paramiko.WarningPolicy())
        self._client.connect(
            hostname=SSH_HOST,
            port=SSH_PORT,
            username=SSH_USER,
            key_filename=SSH_KEY,
            # password=SSH_PWD,
        )

    def __del__(self):
        # SSH切断処理
        self._client.close()

    def search_event(self):
        """
        イベントサーチAPI
        Request URL:
            https://connpass.com/api/v1/event/?keyword=hoge
        """
        pass

    def get_user(self, user_list: list[str]) -> list[dict]:
        """
        ユーザーAPI
        Request URL:
            https://connpass.com/api/v1/user/nickname=:nickname1,:nickname2
            https://connpass.com/api/v1/user/nickname=:nickname1&nickname=:nickname2
        """
        res = []

        # APIをCOUNT件ずつ叩く
        for i in range(0, len(user_list), COUNT):
            channel = self._client.get_transport().open_session(timeout=30)
            try:
                tmp_user_list = user_list[i: i + COUNT]
                api_url = [
                    r'https://connpass.com/api/v1/user/?',
                    'nickname=', ','.join(tmp_user_list),
                    '&count=', str(COUNT)
                ]

                cmd = [
                    'curl',
                    ''.join(api_url)
                ]

                stdout_data = b''
                stderr_data = b''
                print(' '.join(cmd))
                channel.exec_command(' '.join(cmd))

                while not channel.closed or channel.recv_ready() or channel.recv_stderr_ready():
                    stdout_data += channel.recv(RECV_SIZE)
                    stderr_data += channel.recv_stderr(RECV_SIZE)

                code = channel.recv_exit_status()
                print(stdout_data.decode())

                # 標準出力をdictにして取り出し
                data = json.loads(stdout_data.decode())
                if len(tmp_user_list) != data['results_returned']:
                    # APIに問い合わせたユーザ数と返されたユーザ数が一致しない
                    print(f'len(tmp_user_list): {len(tmp_user_list)}')
                    print(f'data["results_returned"]: {data["results_returned"]}')

                res.extend(data.get('users'))
            finally:
                channel.close()

        return res

    def get_user_group(self):
        """
        ユーザー所属グループAPI
        Request URL:
            https://connpass.com/api/v1/user/:nickname/group/
        """
        pass

    def get_user_attended_event(self):
        """
        ユーザー参加イベントAPI
        Request URL:
            https://connpass.com/api/v1/user/:nickname/attended_event/
        """
        pass
