from pathlib import Path

from user import UserManager
from nametag import generate_name_tag


def main() -> None:
    # 生成先のベースディレクトリパス
    # このディレクトリに csv ファイルを含める
    base_dir_path = r''

    # connpass CSV ファイル名
    csv_file_name = 'data.csv'

    if not base_dir_path:
        base_dir_path = str(Path(__file__).parent)

    # ユーザ管理用クラスのインスタンス作成
    um = UserManager(base_dir_path)

    # CSV をロード
    csv_file_path = str(Path(base_dir_path) / csv_file_name)
    um.load(csv_file_path)

    # アイコンをダウンロード
    um.download_icon(over_write=False)

    # ユーザ単位で名札を生成
    for user in um.user_list:
        generate_name_tag(user, base_dir_path, over_write=True)


if __name__ == '__main__':
    main()
