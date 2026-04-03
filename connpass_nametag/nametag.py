import os
import barcode
from pathlib import Path
from barcode.writer import ImageWriter
from PIL import Image, ImageFont, ImageDraw

from user import User
import util_pil as util

# ベース画像
BASE_NAME_TAG_PATH = str(Path(__file__).parent / 'assets' / 'images' / 'base_hagaki.png')
# ベース画像のサイズ (単位: mm) (はがきサイズを想定)
BASE_NAME_TAG_WIDTH = 100
BASE_NAME_TAG_HEIGHT = 148
# デフォルトアイコン画像 (アイコンが取得できなかった場合に使用される)
DEFAULT_ICON_PATH = str(Path(__file__).parent / 'assets' / 'images' / 'default_icon.png')
# フォント
FONT_REGULAR_PATH = str(Path(__file__).parent / 'assets' / 'fonts' / 'NotoSansJP-Regular.ttf')
FONT_MEDIUM_PATH = str(Path(__file__).parent / 'assets' / 'fonts' / 'NotoSansJP-Medium.ttf')
FONT_BOLD_PATH = str(Path(__file__).parent / 'assets' / 'fonts' / 'NotoSansJP-Bold.ttf')


def generate_name_tag(user: User, base_dir_path: str | None = None, over_write: bool = False) -> None:
    """名札画像を生成

    Args:
        user (User): User クラスのインスタンス
        over_write (bool): 上書きするか否か
        base_dir_path (str): 生成先のベースディレクトリのパス
    """
    # 名札保存ディレクトリのパス
    if base_dir_path is None:
        base_dir_path = str(Path(__file__).parent)
    name_tag_dir_path = str(Path(base_dir_path) / 'name_tag')
    # 名札保存ディレクトリを作成
    Path(name_tag_dir_path).mkdir(exist_ok=True)
    # 名札のパス
    name_tag_path = str(Path(name_tag_dir_path) / f'{user.user_name}-{user.rcpt_number}.png')

    # 生成済みか否かを確認
    if Path(name_tag_path).is_file():
        # 上書きを許可していない場合
        if not over_write:
            print('Already generate name tag. Skip generate.')
            return

    # ################################################################
    # ベース画像を読み込み
    # ################################################################
    # 横:100mm 縦:148mm
    base_img = Image.open(BASE_NAME_TAG_PATH).convert('RGBA')
    # ベース画像のサイズをすべての計算の基準とする
    base_img_size = base_img.size
    # ################################################################

    # ################################################################
    # 表示名
    # ################################################################
    # ベースと同じサイズで表示名用の画像を用意
    name_img = Image.new('RGBA', base_img_size)
    draw_name_img = ImageDraw.Draw(name_img)
    # 表示名のフォントサイズを計算
    # 横: 80% 縦:12% 以内に収める
    i = 1
    bbox = draw_name_img.textbbox(
        xy=(0, 0),
        text=user.display_name,
        font=ImageFont.truetype(FONT_BOLD_PATH, i)
    )
    while bbox[2] < base_img_size[0] * 0.80 and bbox[3] < base_img_size[1] * 0.12:
        i += 1
        bbox = draw_name_img.textbbox(
            xy=(0, 0),
            text=user.display_name,
            font=ImageFont.truetype(FONT_BOLD_PATH, i)
        )
    # 表示名の文字を描画
    # 横: 中央 縦: 中央 + 18%
    draw_name_img.text(
        xy=(base_img_size[0] * 0.50, base_img_size[1] * 0.18),
        text=user.display_name,
        fill=(0, 0, 0),
        font=ImageFont.truetype(FONT_BOLD_PATH, i - 1),
        anchor='mm',
    )
    # ################################################################

    # ################################################################
    # 受付番号
    # ################################################################
    """
    # バーコード下に描画したためオミット
    rn_img = Image.new('RGBA', base_img_size)
    draw_dn_img = ImageDraw.Draw(rn_img)

    受付番号の文字を描画
    draw_dn_img.text(
        (30, base_img_size[1] - 20),
        user.rcpt_number,
        fill='black',
        font=ImageFont.truetype(FONT_PATH, 12),
        anchor='mm',
    )
    """
    # ################################################################

    # ################################################################
    # アイコン
    # ################################################################
    # サイズは256x256に角r30px
    if Path(user.icon_path).is_file():
        # ダウンロードしたアイコン画像
        icon_img = Image.open(user.icon_path).convert('RGBA')
    else:
        # デフォルトのアイコン画像
        icon_img = Image.open(DEFAULT_ICON_PATH).convert('RGBA')

    # 余白を足して正方形に
    # icon_img = util.expand2square(icon_img, (255, 255, 255, 0))
    # クロップして正方形に
    icon_img = util.crop_square(icon_img)
    # リサイズ 54x54mm
    icon_size = (
        round(base_img_size[0] / BASE_NAME_TAG_WIDTH * 54),
        round(base_img_size[0] / BASE_NAME_TAG_WIDTH * 54)
    )
    icon_img = icon_img.resize(icon_size)

    # 四隅のピクセルから角丸加工の有無を判定
    round_flag = True
    # 四隅のピクセルが透明か否か
    if icon_img.getpixel((0, 0))[3] == 0 or \
            icon_img.getpixel((icon_img.size[0] - 1, 0)) == 0 or \
            icon_img.getpixel((0, icon_img.size[1] - 1)) == 0 or \
            icon_img.getpixel((icon_img.size[0] - 1, icon_img.size[1] - 1)) == 0:
        round_flag = False

    # ベースと同じサイズに拡張
    # 横: 中央 縦:上から45%
    icon_img = util.add_margin(
        in_img=icon_img,
        top=round((base_img_size[1] - icon_img.size[1]) * 0.45),
        left=round((base_img_size[0] - icon_img.size[0]) * 0.50),
        bottom=round((base_img_size[1] - icon_img.size[1] - (base_img_size[1] - icon_img.size[1]) * 0.45)),
        right=round((base_img_size[0] - icon_img.size[0] - (base_img_size[0] - icon_img.size[0]) * 0.50)),
        color=(0, 0, 0, 0)
    )

    # ベースと同じサイズに拡張した結果サイズが1pxオーバーした場合の処理
    if base_img_size[0] != icon_img.size[0] or base_img_size[1] != icon_img.size[1]:
        # ベースのサイズで中央をクロップ
        icon_img = util.crop_center(icon_img, base_img_size[0], base_img_size[1])

    # 角丸用マスク
    icon_msk_img = Image.new(mode='L', size=base_img_size, color=255)
    if round_flag:
        # 角丸: 2.2mm
        radius = round(base_img_size[0] / BASE_NAME_TAG_WIDTH * 2.2)
        draw_icon_msk_img = ImageDraw.Draw(icon_msk_img)
        # 横: 中央 縦:上から45%
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
    # ################################################################

    # ################################################################
    # 参加区分
    # ################################################################
    # ベースと同じサイズで参加区分用の画像を用意
    category_img = Image.new('RGBA', base_img_size, (0, 0, 0, 0))
    draw_category_img = ImageDraw.Draw(category_img)
    # 上から 104mm の位置に幅 100mm 高さ 15mm の長方形を描画
    draw_category_img.rectangle(
        (0,
         base_img_size[1] / BASE_NAME_TAG_HEIGHT * 104,
         base_img_size[0],
         base_img_size[1] / BASE_NAME_TAG_HEIGHT * (104 + 15)),
        fill=user.category_color,
    )
    # 長方形の中に参加区分のテキストを描画
    # 左右中央 上から 111mm の位置
    draw_category_img.text(
        xy=(base_img_size[0] * 0.50, base_img_size[1] / BASE_NAME_TAG_HEIGHT * 111),
        text=user.category_name,
        fill=(255, 255, 255),
        font=ImageFont.truetype(FONT_MEDIUM_PATH, 100),
        anchor='mm',
    )
    # ################################################################

    # ################################################################
    # QRコード
    # ################################################################
    """
    # バーコードで代替したためオミット
    qr = qrcode.QRCode(box_size=2)
    qr.add_data(user.rcpt_number)
    qr.make()
    qr_img = qr.make_image()
    qr_img = qr_img.resize((200, 200))
    qr_pos = (base_img_size[0] - qr_img.size[0], base_img_size[1] - qr_img.size[1])
    """
    # ################################################################

    # ################################################################
    # バーコード
    # ################################################################
    # バーコード画像を作成して tmp_bc.png というファイル名で一時保存
    tmp_barcode = barcode.Code128(user.rcpt_number, writer=ImageWriter())
    tmp_barcode.save(
        filename='tmp_bc',
        options={
            'module_width': 1,
            # 'font_size': 0,
            # どこかのタイミングでバーコード下の文字の描画をフォントサイズ0で無効化できなくなった
        },
        text=' ',  # このテキストに空白を入れることで文字の描画を無効化できる
    )
    # 一時保存したバーコード画像を開く
    code_img = Image.open('tmp_bc.png').convert('RGBA')
    # 60x10mm にリサイズ
    code_img = code_img.resize((
        int(base_img_size[0] / BASE_NAME_TAG_WIDTH * 60),
        int(base_img_size[1] / BASE_NAME_TAG_HEIGHT * 10)
    ))
    # 上下に 70px ずつマージンを追加
    code_img = util.add_margin(
        in_img=code_img,
        top=70,
        right=0,
        bottom=70,
        left=0,
        color=(0, 0, 0, 0)
    )
    draw_code_img = ImageDraw.Draw(code_img)
    # バーコードの上にユーザ名のテキストを追加
    # 左右中央 上から 3.5mm
    draw_code_img.text(
        xy=(code_img.size[0] * 0.50, base_img_size[1] / BASE_NAME_TAG_HEIGHT * 3.5),
        text=user.user_name,
        fill=(0, 0, 0),
        font=ImageFont.truetype(FONT_REGULAR_PATH, size=30),
        anchor='mm',
    )
    # バーコードの下に受付番号のテキストを追加
    # 左右中央 下から 7mm
    draw_code_img.text(
        xy=(code_img.size[0] * 0.50, code_img.size[1] - (base_img_size[1] / BASE_NAME_TAG_HEIGHT * 7)),
        text=user.rcpt_number,
        fill=(0, 0, 0),
        font=ImageFont.truetype(FONT_REGULAR_PATH, size=30),
        anchor='mm',
    )
    # 右: 5mm 下: 2mm の余白を追加してベースと同じサイズに拡張
    code_img = util.add_margin(
        in_img=code_img,
        top=round((base_img_size[1] - code_img.size[1]) - (base_img_size[1] / BASE_NAME_TAG_HEIGHT * 2)),  # top
        right=round(base_img_size[0] / BASE_NAME_TAG_WIDTH * 5),  # right
        bottom=round(base_img_size[1] / BASE_NAME_TAG_HEIGHT * 2),  # bottom
        left=round((base_img_size[0] - code_img.size[0]) - (base_img_size[0] / BASE_NAME_TAG_WIDTH * 5)),  # left
        color=(0, 0, 0, 0)
    )
    # ################################################################

    # ################################################################
    # コンポジット
    # ################################################################
    # 表示名をアルファブレンド
    res_img = Image.alpha_composite(base_img, name_img)

    # アイコンをコンポジット
    if round_flag:
        # 角丸加工が必要な場合はマスクを使用してコンポ
        res_img = Image.composite(res_img, icon_img, icon_msk_img)
    else:
        # 角丸加工が不要な場合はアルファブレンド
        res_img = Image.alpha_composite(res_img, icon_img)

    # 参加区分をアルファブレンド
    res_img = Image.alpha_composite(res_img, category_img)

    # バーコードを貼り付け
    res_img = Image.alpha_composite(res_img, code_img)
    # ################################################################

    # ################################################################
    # 保存
    # ################################################################
    res_img.convert('RGB').save(name_tag_path)
    print(f'Generate name tag: {name_tag_path}')
    # ################################################################

    # ################################################################
    # 後処理
    # ################################################################
    # バーコード用一時ファイルを削除
    try:
        os.remove('tmp_bc.png')
    except PermissionError as e:
        print(e)
    # ################################################################
