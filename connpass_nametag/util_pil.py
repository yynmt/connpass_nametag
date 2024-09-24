from typing import Union
from PIL import Image


# 上下左右にマージンを付け足し
def add_margin(pil_img: Image, top: int, right: int, bottom: int, left: int,
               color: Union[float, tuple[float, ...]]) -> Image:
    width, height = pil_img.size
    new_width = width + right + left
    new_height = height + top + bottom
    result = Image.new(pil_img.mode, (new_width, new_height), color)
    result.paste(pil_img, (left, top))
    return result


# 正方形になるよう拡張
def expand_square(pil_img: Image, background_color: Union[float, tuple[float, ...]]) -> Image:
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


# 正方形にクロップ
def crop_square(pil_img: Image) -> Image:
    width, height = pil_img.size
    if width == height:
        return pil_img
    elif width > height:
        return pil_img.crop(((width - height) // 2, 0, ((width + height) // 2), height))
    else:
        return pil_img.crop((0, (height - width) // 2, width, (height + width) // 2))


# 中央をクロップ
def crop_center(pil_img: Image, crop_width: int, crop_height: int) -> Image:
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))


# 横に連結
def concat_h(im1: Image, im2: Image) -> Image:
    dst = Image.new('RGB', (im1.width + im2.width, im1.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (im1.width, 0))
    return dst


# 縦に連結
def concat_v(im1: Image, im2: Image) -> Image:
    dst = Image.new('RGB', (im1.width, im1.height + im2.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (0, im1.height))
    return dst
