import os
import csv
import qrcode
import barcode
from pathlib import Path
from barcode.writer import ImageWriter
from PIL import Image, ImageFont, ImageDraw

from user import User
from connpass_api import ConnpassAPI
from util_pil import add_margin, crop_square, crop_center, expand_square

# アイコン画像保存用ディレクトリ
ICON_DIR_PATH = str(Path(__name__).parent / 'icon')
Path(ICON_DIR_PATH).mkdir(exist_ok=True)
# 名札画像生成用ディレクトリ
NAME_TAG_DIR_PATH = str(Path(__name__).parent / 'name_tag')
Path(NAME_TAG_DIR_PATH).mkdir(exist_ok=True)

# connpass CSVファイル
CSV_PATH = r'data.csv'
# ベース画像
BASE_NAME_TAG_PATH = r'assets/base_hagaki.png'
# デフォルトアイコン画像
DEFAULT_ICON_PATH = r'assets/default_icon.png'
# フォント
FONT_PATH_R = r'assets/fonts/NotoSansJP-Regular.ttf'
FONT_PATH_M = r'assets/fonts/NotoSansJP-Medium.ttf'
FONT_PATH_B = r'assets/fonts/NotoSansJP-Bold.otf'


def load_csv(csv_path: str) -> dict[str, User]:
    tmp_part_dict = {}

    # connpassからダウンロードできるcsvファイルはUTF-8
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.reader(f)
        # 1行目のヘッダーをスキップ
        next(reader)

        # 1行ずつ読み込み
        for row in reader:
            u = User('')
            # 参加枠名
            u.category = row[0]
            # ユーザー名
            u.user_name = row[1]
            # 表示名
            u.display_name = row[2]
            # 参加ステータス
            u.status_part = row[5]
            # 受付番号
            u.rcpt_number = row[11]

            # 参加ステータスがキャンセルの参加者は除外
            if 'キャンセル' in u.status_part:
                continue

            # 退会済ユーザーは除外
            if '(退会ユーザー)' in u.user_name:
                continue

            # リストに参加者を追加
            tmp_part_dict[u.user_name] = u

    c_api = ConnpassAPI()
    tmp_connpass_dict_list = c_api.get_user(list(tmp_part_dict.keys()))

    for u in tmp_part_dict.values():
        u.get_connpass_icon_url(tmp_connpass_dict_list)

    return tmp_part_dict


def gen_name_tag(user: User, over_write=False) -> None:
    # 名札保存先のパス
    name_tag_path = Path(NAME_TAG_DIR_PATH) / f'{user.user_name}-{user.rcpt_number}.png'

    # 生成済みか否かを確認
    if Path(name_tag_path).is_file():
        print('Already generate name tag')
        # 上書きを許可していない場合
        if not over_write:
            print('Skip generate')
            return

    # ベース画像を読み込み
    # 横:100mm 縦:148mm
    base_img = Image.open(BASE_NAME_TAG_PATH).convert('RGBA')
    # ベース画像のサイズをすべての計算の基準とする
    base_img_size = base_img.size

    # 表示名
    dn_img = Image.new('RGBA', base_img_size)
    draw_dn_img = ImageDraw.Draw(dn_img)

    # 表示名のフォントサイズを計算
    # 横:80% 縦:10%に収まる
    i = 1
    bbox = draw_dn_img.textbbox(
        xy=(0, 0),
        text=user.display_name,
        font=ImageFont.truetype(FONT_PATH_B, i)
    )
    while bbox[2] < base_img_size[0] * 0.80 and bbox[3] < base_img_size[1] * 0.12:
        i += 1
        bbox = draw_dn_img.textbbox(
            xy=(0, 0),
            text=user.display_name,
            font=ImageFont.truetype(FONT_PATH_B, i)
        )

    # 表示名の文字を描画
    # 横: 中央 縦:中央 + 20%
    draw_dn_img.text(
        xy=(base_img_size[0] * 0.50, base_img_size[1] * 0.18),
        text=user.display_name,
        fill=(0, 0, 0),
        font=ImageFont.truetype(FONT_PATH_B, i - 1),
        anchor='mm',
    )

    # 受付番号
    # rn_img = Image.new('RGBA', base_img_size)
    # draw_dn_img = ImageDraw.Draw(rn_img)

    # 受付番号の文字を描画
    # draw_dn_img.text(
    #     (30, base_img_size[1] - 20),
    #     user.rcpt_number,
    #     fill='black',
    #     font=ImageFont.truetype(FONT_PATH, 12),
    #     anchor='mm',
    # )

    # アイコン
    # サイズは256x256に角r30px
    if Path(user.icon_path).is_file():
        # ダウンロードしたアイコン画像
        icon_img = Image.open(user.icon_path).convert('RGBA')
    else:
        # デフォルトのアイコン画像
        icon_img = Image.open(DEFAULT_ICON_PATH).convert('RGBA')

    # 余白を足して正方形に
    # icon_img = expand2square(icon_img, (255, 255, 255, 0))
    # クロップして正方形に
    icon_img = crop_square(icon_img)
    # リサイズ 54x54mm
    icon_size = (
        round(base_img_size[0] / 100 * 54),
        round(base_img_size[0] / 100 * 54)
    )
    icon_img = icon_img.resize(icon_size)

    # 四隅のピクセルから角丸加工の有無を判定
    round_flag = True
    # 四隅のピクセルが透明か否か
    if icon_img.getpixel((0, 0))[3] == 0 or \
            icon_img.getpixel((icon_img.size[0] - 1, 0)) == 0 or \
            icon_img.getpixel((0, icon_img.size[1] - 1)) == 0 or \
            icon_img.getpixel((icon_img.size[0]-1, icon_img.size[1]-1)) == 0:
        round_flag = False

    # ベースと同じサイズに拡張
    # 横: 中央 縦:上から40%
    icon_img = add_margin(
        pil_img=icon_img,
        top=round((base_img_size[1] - icon_img.size[1]) * 0.45),
        left=round((base_img_size[0] - icon_img.size[0]) * 0.50),
        bottom=round((base_img_size[1] - icon_img.size[1] - (base_img_size[1] - icon_img.size[1]) * 0.45)),
        right=round((base_img_size[0] - icon_img.size[0] - (base_img_size[0] - icon_img.size[0]) * 0.50)),
        color=(0, 0, 0, 0)
    )

    # ベースと同じサイズに拡張した結果サイズが1pxオーバーした場合の処理
    if base_img_size[0] != icon_img.size[0] or base_img_size[1] != icon_img.size[1]:
        # ベースのサイズで中央をクロップ
        icon_img = crop_center(icon_img, base_img_size[0], base_img_size[1])

    # 角丸用マスク
    icon_msk_img = Image.new(mode='L', size=base_img_size, color=255)
    if round_flag:
        # 角丸: 2.2mm
        radius = round(base_img_size[0] / 100 * 2.2)
        draw_icon_msk_img = ImageDraw.Draw(icon_msk_img)
        draw_icon_msk_img.rounded_rectangle(
            (round((base_img_size[0] - icon_size[0]) * 0.50) + 1,
             round((base_img_size[1] - icon_size[1]) * 0.45) + 1,
             round((base_img_size[0] - icon_size[0]) * 0.50) + icon_size[0] - 1,
             round((base_img_size[1] - icon_size[1]) * 0.45) + icon_size[1] - 1),
            radius=radius,
            fill=0,
            outline=None,
            width=0
        )

    # 参加区分
    text_category = user.DEFAULT_CATEGORY_TEXT
    color_category = user.DEFAULT_CATEGORY_COLOR
    if user.category == 'スタッフ':
        text_category = 'STAFF'
        color_category = user.CATEGORY['STAFF']
    elif user.category == 'プレス':
        text_category = 'PRESS'
        color_category = user.CATEGORY['PRESS']
    elif user.category == 'スポンサー':
        text_category = 'SPONSOR'
        color_category = user.CATEGORY['SPONSOR']

    category_img = Image.new('RGBA', base_img_size, (0, 0, 0, 0))
    draw_category_img = ImageDraw.Draw(category_img)
    draw_category_img.rectangle(
        (0,
         base_img_size[1] / 148 * 104,
         base_img_size[0],
         base_img_size[1] / 148 * 119),
        fill=color_category,
    )
    draw_category_img.text(
        xy=(base_img_size[0] * 0.50, base_img_size[1] / 148 * 111),
        text=text_category,
        fill=(255, 255, 255),
        font=ImageFont.truetype(FONT_PATH_M, 100),
        anchor='mm',
    )

    # QRコード
    # qr = qrcode.QRCode(box_size=2)
    # qr.add_data(user.rcpt_number)
    # qr.make()
    # qr_img = qr.make_image()
    # qr_img = qr_img.resize((200, 200))
    # qr_pos = (base_img_size[0] - qr_img.size[0], base_img_size[1] - qr_img.size[1])

    # バーコード
    tmp_barcode = barcode.Code128(user.rcpt_number, writer=ImageWriter())
    tmp_barcode.save(
        filename='tmp_bc',
        options={
            'module_width': 1,
            # 'font_size': 0 <- どこかのタイミングでバーコード下の文字の描画をフォントサイズ0で無効化できなくなった
        },
        text=' ',   # ここのテキストに空白を入れることで↑の対策ができる
    )
    code_img = Image.open('tmp_bc.png').convert('RGBA')
    code_img = code_img.resize((600, 100))
    # bc_pos = (base_img_size[0] - bc_img.size[0], base_img_size[1] - bc_img.size[1])

    code_img = add_margin(
        pil_img=code_img,
        top=70,
        right=0,
        bottom=70,
        left=0,
        color=(0, 0, 0, 0)
    )

    draw_code_img = ImageDraw.Draw(code_img)
    draw_code_img.text(
        xy=(code_img.size[0] * 0.50, 50),
        text=user.user_name,
        fill=(0, 0, 0),
        font=ImageFont.truetype(FONT_PATH_R, size=30),
        anchor='mm',
    )

    draw_code_img.text(
        xy=(code_img.size[0] * 0.50, code_img.size[1] - 50),
        text=user.rcpt_number,
        fill=(0, 0, 0),
        font=ImageFont.truetype(FONT_PATH_R, size=30),
        anchor='mm',
    )

    # 右:5mm 下:2mm 余白
    code_img = add_margin(
        pil_img=code_img,
        top=round((base_img_size[1] - code_img.size[1]) - (base_img_size[1] / 148 * 2)),  # top
        right=round(base_img_size[0] / 100 * 5),  # right
        bottom=round(base_img_size[1] / 148 * 2),  # bottom
        left=round((base_img_size[0] - code_img.size[0]) - (base_img_size[0] / 100 * 5)),  # left
        color=(0, 0, 0, 0)
    )

    # 表示名をアルファブレンド
    res_img = Image.alpha_composite(base_img, dn_img)

    # 受付番号をアルファブレンド
    # res_img = Image.alpha_composite(res_img, rn_img)

    # アイコンをコンポジット
    if round_flag:
        # 角丸加工が必要な場合はマスクを使用してコンポ
        res_img = Image.composite(res_img, icon_img, icon_msk_img)
    else:
        # 角丸加工が不要な場合はアルファブレンド
        res_img = Image.alpha_composite(res_img, icon_img)

    # 参加区分をアルファブレンド
    res_img = Image.alpha_composite(res_img, category_img)

    # QRコードを貼り付け
    # res_img.paste(qr_img, qr_pos)

    # バーコードを貼り付け
    res_img = Image.alpha_composite(res_img, code_img)
    # res_img.paste(bc_img, bc_pos)

    # 保存
    res_img.convert('RGB').save(name_tag_path)
    print(f'Generate name tag: {name_tag_path}')

    # バーコード用一時ファイルを削除
    os.remove('tmp_bc.png')


if __name__ == '__main__':
    # CSVを読み込み
    part_dict = load_csv(CSV_PATH)

    for uid, user in part_dict.items():
        # アイコンをダウンロード
        user.download_icon(skip=False, over_write=True)
        # 名札を生成
        gen_name_tag(user, over_write=True)
        # break
