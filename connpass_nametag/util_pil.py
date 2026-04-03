from PIL import Image


def add_margin(in_img: Image, top: int, right: int, bottom: int, left: int,
               color: float | tuple[float, ...]) -> Image:
    """入力画像の上下左右に任意のマージンを拡張

    Args:
        in_img: 入力画像
        top (int): 上方向のマージン (px)
        right (int): 右方向のマージン (px)
        bottom (int): 下方向のマージン (px)
        left (int): 左方向のマージン (px)
        color (float|tuple[float, ...]): マージンの色
    Returns:
        Image: 出力画像
    """
    width, height = in_img.size
    new_width = width + right + left
    new_height = height + top + bottom
    out_img = Image.new(in_img.mode, (new_width, new_height), color)
    out_img.paste(in_img, (left, top))
    return out_img


def expand_square(in_img: Image, background_color: float | tuple[float, ...]) -> Image:
    """入力画像を正方形に拡張

    Args:
        in_img: 入力画像
        background_color (float|tuple[float, ...]): 背景色色
    Returns:
        Image: 出力画像
    """
    width, height = in_img.size
    if width == height:
        return in_img
    elif width > height:
        out_img = Image.new(in_img.mode, (width, width), background_color)
        out_img.paste(in_img, (0, (width - height) // 2))
        return out_img
    else:
        out_img = Image.new(in_img.mode, (height, height), background_color)
        out_img.paste(in_img, ((height - width) // 2, 0))
        return out_img


def crop_square(in_img: Image) -> Image:
    """入力画像を正方形にクロップ

    Args:
        in_img: 入力画像
    Returns:
        Image: 出力画像
    """
    width, height = in_img.size
    if width == height:
        return in_img
    elif width > height:
        return in_img.crop(((width - height) // 2, 0, ((width + height) // 2), height))
    else:
        return in_img.crop((0, (height - width) // 2, width, (height + width) // 2))


def crop_center(in_img: Image, crop_width: int, crop_height: int) -> Image:
    """入力画像の中央をクロップ

    Args:
        in_img: 入力画像
        crop_width: クロップする幅
        crop_height: クロップする高さ
    Returns:
        Image: 出力画像
    """
    img_width, img_height = in_img.size
    return in_img.crop(((img_width - crop_width) // 2,
                        (img_height - crop_height) // 2,
                        (img_width + crop_width) // 2,
                        (img_height + crop_height) // 2))


def concat_h(in_img1: Image, in_img2: Image) -> Image:
    """入力画像1と入力画像2を横方向に連結

    Args:
        in_img1: 入力画像2
        in_img2: 入力画像2
    Returns:
        Image: 出力画像
    """
    out_img = Image.new('RGB', (in_img1.width + in_img2.width, in_img1.height))
    out_img.paste(in_img1, (0, 0))
    out_img.paste(in_img2, (in_img1.width, 0))
    return out_img


def concat_v(in_img1: Image, in_img2: Image) -> Image:
    """入力画像1と入力画像2を縦方向に連結

    Args:
        in_img1: 入力画像2
        in_img2: 入力画像2
    Returns:
        Image: 出力画像
    """
    out_img = Image.new('RGB', (in_img1.width, in_img1.height + in_img2.height))
    out_img.paste(in_img1, (0, 0))
    out_img.paste(in_img2, (0, in_img1.height))
    return out_img
