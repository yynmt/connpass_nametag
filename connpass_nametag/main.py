import csv
import qrcode
import barcode
from pathlib import Path
from barcode.writer import ImageWriter
from PIL import Image, ImageFont, ImageDraw

from user import User
from connpass_api import ConnpassAPI
from util_pil import add_margin, crop_square, crop_center, expand_square, concat_v, concat_h

# アイコン画像保存用ディレクトリ
ICON_DIR_PATH = str(Path(__name__).parent / 'icon')
# 名札画像生成用ディレクトリ
NAME_TAG_DIR_PATH = str(Path(__name__).parent / 'name_tag')
# 名札画像
CONCAT_DIR_PATH = str(Path(__name__).parent / 'concat')
Path(ICON_DIR_PATH).mkdir(exist_ok=True)
Path(NAME_TAG_DIR_PATH).mkdir(exist_ok=True)
Path(CONCAT_DIR_PATH).mkdir(exist_ok=True)

CSV_PATH = r'data.csv'
BASE_NAME_TAG_PATH = r'base_hagaki.png'
DEFAULT_ICON_PATH = r'default_icon.png'
DUMMY_IMG_PATH = r'dummy.png'

FONT_PATH_R = r'fonts/NotoSansJP-Regular.ttf'
FONT_PATH_M = r'fonts/NotoSansJP-Medium.ttf'
FONT_PATH_B = r'fonts/NotoSansJP-Bold.otf'


def load_csv(csv_path):
    tmp_part_dict = {}

    # connpassからダウンロードできるcsvファイルはShift-JIS
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.reader(f)
        # 1行目のヘッダーをスキップ
        next(reader)

        # 1行ずつ読み込み
        for row in reader:
            user = User('')
            # 参加枠名
            user.category = row[0]
            # ユーザー名
            user.user_name = row[1]
            # 表示名
            user.display_name = row[2]
            # 参加ステータス
            user.status_part = row[5]
            # 受付番号
            user.rcpt_number = row[10]

            # 参加ステータスがキャンセルの参加者は除外
            if 'キャンセル' in user.status_part:
                continue

            # 退会済ユーザーは除外
            if '(退会ユーザー)' in user.user_name:
                continue

            # リストに参加者を追加
            tmp_part_dict[user.user_name] = user

    c_api = ConnpassAPI()
    tmp_connpass_dict_list = c_api.get_user(list(tmp_part_dict.keys()))

    for user in tmp_part_dict.values():
        user.get_connpass_icon_url(tmp_connpass_dict_list)

    return tmp_part_dict


def gen_name_tag(user, over_write=False):
    # 名札保存先のパス
    name_tag_path = Path(NAME_TAG_DIR_PATH) / '{}-{}.png'.format(user.user_name, user.rcpt_number)

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
    bbox = draw_dn_img.textbbox((0, 0), user.display_name, font=ImageFont.truetype(FONT_PATH_B, i))
    while bbox[2] < base_img_size[0] * 0.80 and bbox[3] < base_img_size[1] * 0.12:
        i += 1
        bbox = draw_dn_img.textbbox((0, 0), user.display_name, font=ImageFont.truetype(FONT_PATH_B, i))

    # 表示名の文字を描画
    # 横: 中央 縦:中央 + 20%
    draw_dn_img.text(
        (base_img_size[0] * 0.50, base_img_size[1] * 0.18),
        user.display_name,
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
        icon_img,
        round((base_img_size[1] - icon_img.size[1]) * 0.45),   # top
        round((base_img_size[0] - icon_img.size[0]) * 0.50),   # right
        round((base_img_size[1] - icon_img.size[1] - (base_img_size[1] - icon_img.size[1]) * 0.45)),   # bottom
        round((base_img_size[0] - icon_img.size[0] - (base_img_size[0] - icon_img.size[0]) * 0.50)),   # left
        (0, 0, 0, 0))

    # ベースと同じサイズに拡張した結果サイズが1pxオーバーした場合の処理
    if base_img_size[0] != icon_img.size[0] or base_img_size[1] != icon_img.size[1]:
        # ベースのサイズで中央をクロップ
        icon_img = crop_center(icon_img, base_img_size[0], base_img_size[1])

    if round_flag:
        # 角丸: 2.2mm
        radius = round(base_img_size[0] / 100 * 2.2)
        # 角丸用マスク
        icon_msk_img = Image.new('L', base_img_size, 255)
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
        (base_img_size[0] * 0.50, base_img_size[1] / 148 * 111),
        text_category,
        fill=(255, 255, 255),
        font=ImageFont.truetype(FONT_PATH_M, 100),
        anchor='mm',
    )
    # draw.rectangle((200, 100, 300, 200), fill=(0, 192, 192), outline=(255, 255, 255))

    # QRコード
    # qr = qrcode.QRCode(box_size=2)
    # qr.add_data(user.rcpt_number)
    # qr.make()
    # qr_img = qr.make_image()
    # qr_img = qr_img.resize((200, 200))
    # qr_pos = (base_img_size[0] - qr_img.size[0], base_img_size[1] - qr_img.size[1])

    # バーコード

    # a = barcode.get_barcode_class('code128')
    # a.render(writer_options=None, text=None)

    tmp_barcode = barcode.Code128(user.rcpt_number, writer=ImageWriter())
    tmp_barcode.save(
        'tmp_bc',
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
        code_img,
        70,
        0,
        70,
        0,
        (0, 0, 0, 0)
    )

    draw_code_img = ImageDraw.Draw(code_img)
    draw_code_img.text(
        (code_img.size[0] * 0.50, 50),
        user.user_name,
        fill=(0, 0, 0),
        font=ImageFont.truetype(FONT_PATH_R, 30),
        anchor='mm',
    )

    draw_code_img.text(
        (code_img.size[0] * 0.50, code_img.size[1] - 50),
        user.rcpt_number,
        fill=(0, 0, 0),
        font=ImageFont.truetype(FONT_PATH_R, 30),
        anchor='mm',
    )

    # 右:5mm 下:2mm 余白
    code_img = add_margin(
        code_img,
        round((base_img_size[1] - code_img.size[1]) - (base_img_size[1] / 148 * 2)),  # top
        round(base_img_size[0] / 100 * 5),  # right
        round(base_img_size[1] / 148 * 2),  # bottom
        round((base_img_size[0] - code_img.size[0]) - (base_img_size[0] / 100 * 5)),  # left
        (0, 0, 0, 0)
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

    # 参加区分を貼り付け
    res_img = Image.alpha_composite(res_img, category_img)

    # QRコードを貼り付け
    # res_img.paste(qr_img, qr_pos)

    # バーコードを貼り付け
    res_img = Image.alpha_composite(res_img, code_img)
    # res_img.paste(bc_img, bc_pos)

    # 保存
    res_img.convert('RGB').save(name_tag_path)
    # ここで名札画像が生成されて存在しているか確認して存在していなければ例外を出すべき
    print('Generate name tag: {}'.format(name_tag_path))


def concat_nametag(path_list, output_dir, prefix=''):
    # 書き出し画像用カウンタ
    cnt = 0
    # 余白用dummy画像
    dummy_im = Image.open(DUMMY_IMG_PATH)

    it = iter(path_list)
    while True:
        im0_path = im1_path = im2_path = im3_path = im4_path = None
        im5_path = im6_path = im7_path = im8_path = im9_path = None
        try:
            im0_path = next(it)
            im1_path = next(it)
            im2_path = next(it)
            im3_path = next(it)
            im4_path = next(it)
            im5_path = next(it)
            im6_path = next(it)
            im7_path = next(it)
            im8_path = next(it)
            im9_path = next(it)
        except StopIteration:
            break
        finally:
            im0 = Image.open(im0_path) if im0_path and Path(im0_path).is_file() else dummy_im
            im1 = Image.open(im1_path) if im1_path and Path(im1_path).is_file() else dummy_im
            im2 = Image.open(im2_path) if im2_path and Path(im2_path).is_file() else dummy_im
            im3 = Image.open(im3_path) if im3_path and Path(im3_path).is_file() else dummy_im
            im4 = Image.open(im4_path) if im4_path and Path(im4_path).is_file() else dummy_im
            im5 = Image.open(im5_path) if im5_path and Path(im5_path).is_file() else dummy_im
            im6 = Image.open(im6_path) if im6_path and Path(im6_path).is_file() else dummy_im
            im7 = Image.open(im7_path) if im7_path and Path(im7_path).is_file() else dummy_im
            im8 = Image.open(im8_path) if im8_path and Path(im8_path).is_file() else dummy_im
            im9 = Image.open(im9_path) if im9_path and Path(im9_path).is_file() else dummy_im

            # 各名札画像を詰め込み
            res = concat_v(concat_h(im0, im1), concat_h(im2, im3))
            res = concat_v(res, concat_h(im4, im5))
            res = concat_v(res, concat_h(im6, im7))
            res = concat_v(res, concat_h(im8, im9))

            # 余白を追加 左右14mm 上下11mmずつ -> 印刷時の余白が上下5mm発生するので4mm 1mmで計算
            # https://www.a-one.co.jp/product/search/detail.php?id=72110
            # concat後の画像は横182mm 縦275mm
            margin_x = round(res.size[0] / 182 * 4)
            margin_y = round(res.size[1] / 275 * 1)
            res = add_margin(res, margin_y, margin_x, margin_y, margin_x, (57, 57, 57))

            # 保存
            concat_path = str(Path(output_dir) / '{}{:0=3}.png'.format(prefix, cnt))
            res.save(concat_path)
            print('Concat name tag: {}'.format(concat_path))

            cnt += 1


if __name__ == '__main__':
    # CSVを読み込み
    part_dict = load_csv(CSV_PATH)

    for uid, user in part_dict.items():
        # アイコンをダウンロード
        user.download_icon(skip=False, over_write=True)
        # 名札を生成
        gen_name_tag(user, over_write=True)

        # break

    # 表示名順でソートしたリストに変換
    # part_list = list(part_dict.values())
    # part_list.sort(key=lambda x: x.display_name)
    # 表示名順でソートした名札画像のパスリスト
    # nametag_path_list = [str(Path(NAME_TAG_DIR_PATH) / '{}.png'.format(p.user_name)) for p in part_list]
    # 生成した名札を10枚単位でconcat
    # concat_nametag(nametag_path_list, CONCAT_DIR_PATH, 'general')

    # 以下ディレクトリに名札画像(全部同一サイズ)を入れると10枚単位でconcatされる
    # EX_NAME_TAG_DIR_PATH = r'ex_name_tag'
    # glob_p = r'*.png'
    # gr = list(Path(EX_NAME_TAG_DIR_PATH).glob(glob_p))
    # gr = [str(g) for g in gr]
    # concat_nametag(gr, CONCAT_DIR_PATH, 'ex')
