import csv
import time
import requests
from pathlib import Path

from connpass_api import ConnpassAPI

# サーバ負荷軽減のための待機時間 (単位: 秒)
SLEEP_TIME = 1
# カテゴリー名とカテゴリーの色
CATEGORY_MAP = {
    '': ('', (208, 208, 208)),
    'スタッフ': ('STAFF', (195, 13, 35)),
    'プレス': ('PRESS', (0, 160, 233)),
    'スポンサー': ('SPONSOR', (96, 25, 134)),
}


class User:
    """ユーザ

    Attributes:
        __user_name (str): ユーザ名 (connpass の ID)
        __display_name (str): ユーザ表示名
        __rcpt_number (str): 受付番号
        __category (str): 参加枠
        __category_name (str): 参加枠表示名
        __category_color (str): 参加枠表示色
        __icon_dir_path (str): アイコンディレクトリのパス
        __icon_path (str): アイコンパス
        __icon_url (str): アイコンダウンロード URL
    """
    def __init__(self, connpass_id: str, display_name: str, category: str, rcpt_number: str, icon_dir_path: str):
        # ユーザ名 (connpass の ID)
        self.__user_name = connpass_id
        # ユーザ表示名
        self.__display_name = display_name
        # 受付番号
        self.__rcpt_number = rcpt_number

        # 参加枠
        self.__category = category
        try:
            name, color = CATEGORY_MAP[self.__category]
        except KeyError:
            name, color = CATEGORY_MAP['']
        # 参加枠表示名
        self.__category_name = name
        # 参加枠表示色
        self.__category_color = color

        # アイコンディレクトリのパス
        self.__icon_dir_path = icon_dir_path
        # アイコンパス
        self.__icon_path = self.__resolve_icon_path()
        # アイコンダウンロード URL
        self.__icon_url = ''

    @property
    def user_name(self) -> str:
        return self.__user_name

    @property
    def display_name(self) -> str:
        return self.__display_name

    @property
    def category(self) -> str:
        return self.__category

    @property
    def category_name(self) -> str:
        return self.__category_name

    @property
    def category_color(self) -> (int, int, int):
        return self.__category_color

    @property
    def rcpt_number(self) -> str:
        return self.__rcpt_number

    @property
    def icon_path(self) -> str:
        return self.__icon_path

    @property
    def icon_url(self) -> str:
        return self.__icon_url

    @icon_url.setter
    def icon_url(self, url: str) -> None:
        self.__icon_url = url

    def __resolve_icon_path(self) -> str:
        """アイコンのパスを解決
        アイコンがダウンロード済みの場合はそのパスを取得

        Returns:
            str: アイコンのパス
        """
        glob_p = f'{self.__user_name}*.*'
        gr = list(Path(self.__icon_dir_path).glob(glob_p))
        if gr:
            path = str(gr[0])
        else:
            path = str(Path(self.__icon_dir_path) / f'{self.__user_name}-{self.__rcpt_number}.png')

        return path


class UserManager:
    """ユーザ管理

    Attributes:
        __user_dict (dict[User]): ユーザ管理 dict
        __icon_dir_path (str): アイコンディレクトリのパス
    """
    def __init__(self, base_dir_path: str | None = None) -> None:
        """
        Args:
            base_dir_path (str): ベースディレクトリのパス
        """
        self.__user_dict = {}
        if base_dir_path is None:
            base_dir_path = str(Path(__file__).parent)
        self.__icon_dir_path = str(Path(base_dir_path) / 'icon')

    @property
    def user_name_list(self) -> list[str]:
        return list(self.__user_dict.keys())

    @property
    def user_list(self) -> list[User]:
        return list(self.__user_dict.values())

    def clear(self) -> None:
        self.__user_dict = {}

    def load(self, csv_path: str) -> None:
        self.clear()
        # CSV ファイルをロード
        self.__load_csv(csv_path)
        # connpass API でアイコンダウンロード元の URL を解決
        self.__get_icon_url()

    def __load_csv(self, csv_path: str) -> None:
        if not Path(csv_path).is_file():
            return

        __header_map_dict = {
            'category': '参加枠名',
            'user_name': 'ユーザー名',
            'display_name': '表示名',
            'status_part': '参加ステータス',
            'rcpt_number': '受付番号',
        }

        # connpassからダウンロードできるcsvファイルはUTF-8
        with open(csv_path, encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header_index = {}
            # 1行目のヘッダーから列の対応関係を取得
            header = next(reader)
            for k, v in __header_map_dict.items():
                try:
                    i = header.index(v)
                    header_index[k] = i
                except ValueError:
                    continue

            # 2行目以降を1行ずつ読み込み
            for row in reader:
                # ユーザー名 (connpass の ID)
                user_name = row[header_index['user_name']]
                # 表示名
                display_name = row[header_index['display_name']]
                # 参加枠名
                category = row[header_index['category']]
                # 参加ステータス
                status_part = row[header_index['status_part']]
                # 受付番号
                rcpt_number = row[header_index['rcpt_number']]

                # 参加ステータスがキャンセルの参加者は除外
                if 'キャンセル' in status_part:
                    continue

                # 退会済ユーザーは除外
                if '(退会ユーザー)' in user_name:
                    continue

                # リストに参加者を追加
                self.__user_dict[user_name] = User(user_name, display_name, category, rcpt_number, self.__icon_dir_path)

    def __get_icon_url(self) -> None:
        c_api = ConnpassAPI()
        tmp_connpass_dict_list = c_api.get_user(self.user_name_list)

        for c_dict in tmp_connpass_dict_list:
            try:
                user_name = c_dict['nickname']
                user = self.__user_dict[user_name]
                if c_dict['image_url']:
                    user.icon_url = c_dict['image_url']
            except KeyError:
                continue

    def download_icon(self, over_write: bool = False) -> None:
        # アイコンのディレクトリを作成
        Path(self.__icon_dir_path).mkdir(exist_ok=True)

        # ユーザ毎ににアイコンをダウンロードする
        for user in self.__user_dict.values():
            if Path(user.icon_path).is_file():
                if not over_write:
                    print(f'Already download icon: {user.icon_path}')
                    continue

            # サーバー負荷軽減のため待機
            time.sleep(SLEEP_TIME)

            # アイコンの URL が connpass API で取得済みの場合のみ
            if user.icon_url:
                # connpass のアイコンをダウンロード
                response = requests.get(user.icon_url)
                icon_img = response.content
                # _, ext = os.path.splitext(user.icon_url)
                ext = Path(user.icon_url).suffix[1:]
                # ToDo: tmp に一旦保存してそこから保存先へ移動する処理を入れる
                # ToDo: ext が png 以外のときはいい感じに変換する処理を入れる
                print(f'Download icon: {user.icon_url} -> {user.icon_path}')
                with open(user.icon_path, 'wb') as f:
                    f.write(icon_img)
