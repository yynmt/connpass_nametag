import os
import csv
import time
import qrcode
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from PIL import Image, ImageFont, ImageDraw

ICON_DIR_PATH = str(Path(__name__).parent / 'icon')
NAME_TAG_DIR_PATH = str(Path(__name__).parent / 'name_tag')
Path(ICON_DIR_PATH).mkdir(exist_ok=True)
Path(NAME_TAG_DIR_PATH).mkdir(exist_ok=True)

CSV_PATH = r'data.csv'
BASE_NAME_TAG_PATH = 'base.png'
DEFAULT_ICON_PATH = 'default_icon.png'


class NameTag:
    def __init__(self):
        self.user_name = ''
        self.display_name = ''
        self.rcpt_number = -1
        self.icon_path = ''


def get_icon_url(user_id):
    base_url = r'https://connpass.com/user/'

    html_text = requests.get(base_url + user_id).text
    soup = BeautifulSoup(html_text, 'html.parser')

    # 以下に該当する箇所を探索
    # <a class="image_link" href="https://connpass-tokyo.s3.amazonaws.com/user/263056/4e452935ef5542e0ab3452962f52fae8.png">
    # <img src="https://connpass-tokyo.s3.amazonaws.com/thumbs/58/5b/585b69c12cb8be2c2d641f166a93b6f6.png" width="180" height="180" title="◤◢◤◢◤◢◤◢" alt="◤◢◤◢◤◢◤◢">
    # </a>
    els = soup.find_all('a', class_='image_link')
    for el in els:
        att = el.get('href', '')
        if att.endswith('.png') or att.endswith('.jpg'):
            return att


def download_icon(nt, skip=False):
    # アイコンがすでにダウンロード済み
    if nt.icon_path:
        return nt.icon_path

    # アイコンがすでにダウンロード済み
    glob_p = r'{}.*'.format(nt.user_name)
    gr = list(Path(ICON_DIR_PATH).glob(glob_p))
    if gr:
        return str(gr[0])

    # サーバー負荷軽減のためスッキプ
    # デバッグ目的でこれ以降の処理をスキップ
    if skip:
        return ''

    nt.icon_url = get_icon_url(nt.user_name)

    # アイコンのURLが見つからなかった
    if nt.icon_url is None:
        return ''

    _, ext = os.path.splitext(nt.icon_url)
    response = requests.get(nt.icon_url)
    img = response.content
    icon_path = str(Path(__name__).parent / 'icon' / '{}{}'.format(nt.user_name, ext))
    with open(icon_path, "wb") as f:
        f.write(img)

    return icon_path


def load_csv(csv_path):
    tmp_part_dict = {}

    # connpassからダウンロードできるcsvファイルはShift-JIS
    with open(csv_path, encoding='cp932') as f:
        reader = csv.reader(f)
        # 1行目のヘッダーをスキップ
        next(reader)

        # 1行ずつ読み込み
        for row in reader:
            nt = NameTag()
            # ユーザー名
            nt.user_name = row[1]
            # 表示名
            nt.display_name = row[2]
            # 参加ステータス
            status_part = row[5]
            # 受付番号
            nt.rcpt_number = row[10]

            # 参加ステータスがキャンセルの参加者は除外
            if 'キャンセル' in status_part:
                continue

            # リストに参加者を追加
            tmp_part_dict[nt.user_name] = nt

        return tmp_part_dict


def gen_name_tag(nt):
    # 使用フォント
    font = r'asago1.otf'

    # ベースを読み込み
    base_img = Image.open(BASE_NAME_TAG_PATH).convert('RGBA')
    base_img_size = base_img.size

    # 表示名
    dn_img = Image.new('RGBA', base_img_size)
    draw_dn_img = ImageDraw.Draw(dn_img)
    # 黄色の矩形を描画
    draw_dn_img.rectangle(
        [(0, base_img_size[1] / 3), (base_img_size[0], base_img_size[1] * 2 / 3)],
        fill=(255, 220, 0, 128)
    )

    # 表示名のフォントサイズを計算
    i = 1
    bbox = draw_dn_img.textbbox((0, 0), nt.display_name, font=ImageFont.truetype(font, i))
    while bbox[2] < base_img_size[0] * 0.8 and bbox[3] < base_img_size[1] / 3:
        i += 1
        bbox = draw_dn_img.textbbox((0, 0), nt.display_name, font=ImageFont.truetype(font, i))

    # 表示名の文字入れ
    draw_dn_img.text(
        (base_img_size[0] / 2, base_img_size[1] / 2),
        nt.display_name,
        fill='black',
        font=ImageFont.truetype(font, i - 1),
        anchor='mm',
    )

    # 受付番号
    rn_img = Image.new('RGBA', base_img_size)
    draw_dn_img = ImageDraw.Draw(rn_img)

    # 受付番号の文字入れ
    draw_dn_img.text(
        (30, base_img_size[1]-20),
        nt.rcpt_number,
        fill='black',
        font=ImageFont.truetype(font, 12),
        anchor='mm',
    )

    # アイコン
    # アイコンを開いてアイコン部分を作製
    if Path(nt.icon_path).is_file():
        icon_img = Image.open(nt.icon_path).convert('RGBA')
    else:
        icon_img = Image.open(DEFAULT_ICON_PATH).convert('RGBA')

    # 余白を足して正方形に
    icon_img = expand2square(icon_img, (255, 255, 255, 255))
    # リサイズ
    icon_img = icon_img.resize((200, 200))
    # ベースと同じサイズに拡張
    icon_img = add_margin(icon_img, 0, base_img_size[0]-icon_img.size[0], base_img_size[1]-icon_img.size[1], 0, (0, 0, 0, 0))

    # QRコード
    qr = qrcode.QRCode(box_size=2)
    qr.add_data(nt.rcpt_number)
    qr.make()
    qr_img = qr.make_image()
    qr_img = qr_img.resize((200, 200))
    qr_pos = (base_img_size[0] - qr_img.size[0], base_img_size[1] - qr_img.size[1])

    # 表示名をアルファブレンド
    res_img = Image.alpha_composite(base_img, dn_img)
    # 受付番号をアルファブレンド
    res_img = Image.alpha_composite(res_img, rn_img)
    # アイコンをアルファブレンド
    res_img = Image.alpha_composite(res_img, icon_img)
    # QRコードを貼り付け
    res_img.paste(qr_img, qr_pos)

    # 保存
    name_tag_path = Path(NAME_TAG_DIR_PATH) / '{}.png'.format(nt.user_name)
    res_img.convert('RGB').save(name_tag_path)


def add_margin(pil_img, top, right, bottom, left, color):
    width, height = pil_img.size
    new_width = width + right + left
    new_height = height + top + bottom
    result = Image.new(pil_img.mode, (new_width, new_height), color)
    result.paste(pil_img, (left, top))
    return result


def expand2square(pil_img, background_color):
    width, height = pil_img.size
    if width == height:
        return pil_img
    elif width > height:
        result = Image.new(pil_img.mode, (width, width), background_color)
        result.paste(pil_img, (0, (width - height) // 2))
        return result
    else:
        result = Image.new(pil_img.mode, (height, height), background_color)
        result.paste(pil_img, ((height - width) // 2, 0))
        return result


if __name__ == '__main__':
    part_dict = load_csv(CSV_PATH)
    for uid, nt in part_dict.items():
        # アイコンのダウンロード
        nt.icon_path = download_icon(nt, skip=True)
        # 名札の生成
        gen_name_tag(nt)
