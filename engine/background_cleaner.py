"""
Module Tự Động Nhận Diện & Làm Sạch Nền Mẫu (Background Cleaner v4.0)
- Tối ưu hóa đa tầng (Pyramid Inpainting) siêu tốc cho ảnh cưới độ phân giải cao.
- Tự động phát hiện và xóa nhân vật mẫu + xóa lớp phủ giao diện TikTok / Reels (nếu ảnh mẫu chụp màn hình từ TikTok).
"""

import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Optional
from engine.matting import get_matting_engine


def clean_reference_background_bgr(
    bg_bgr: np.ndarray, dilation_radius: int = 25, clean_social_ui: bool = True
) -> Tuple[np.ndarray, bool, Optional[np.ndarray]]:
    """
    Phiên bản OpenCV BGR trực tiếp:
    - Tự động xóa nhân vật trong ảnh nền mẫu (nếu có).
    - Tự động làm sạch watermark/UI TikTok ở góc phải & đáy ảnh (nếu có).
    """
    h, w = bg_bgr.shape[:2]
    engine = get_matting_engine()
    cleaned_border_bgr, _ = engine.detect_and_clean_screenshot_border(bg_bgr)
    alpha_person = engine.extract_alpha_core(cleaned_border_bgr)

    # Kiểm tra xem có thực sự là CON NGƯỜI đứng ở vùng trung tâm ảnh hay chỉ là cụm hoa/cửa sổ của phông nền sạch:
    # Con người trong ảnh mẫu phải nằm ở vùng trung tâm x in [0.32, 0.68], y in [0.15, 0.85] VÀ có vùng da người (YCrCb).
    ycrcb = cv2.cvtColor(cleaned_border_bgr, cv2.COLOR_BGR2YCrCb)
    cr, cb = ycrcb[:, :, 1], ycrcb[:, :, 2]
    skin_mask = (cr >= 133) & (cr <= 176) & (cb >= 77) & (cb <= 128) & (alpha_person > 0.5)

    center_roi = np.zeros_like(alpha_person, dtype=bool)
    center_roi[int(h * 0.14):int(h * 0.75), int(w * 0.32):int(w * 0.68)] = True

    center_fg_ratio = float(np.mean((alpha_person[center_roi] > 0.5)))
    center_skin_ratio = float(np.mean(skin_mask[center_roi]))

    binary_mask = (alpha_person > 0.25).astype(np.uint8) * 255
    has_person = (center_fg_ratio >= 0.18) and (center_skin_ratio >= 0.004)
    if not has_person:
        return cleaned_border_bgr, False, None

    max_dim = max(w, h)
    scale = 1280.0 / max_dim if max_dim > 1280 else 1.0
    inpaint_w = max(int(w * scale), 64)
    inpaint_h = max(int(h * scale), 64)

    small_bgr = cv2.resize(cleaned_border_bgr, (inpaint_w, inpaint_h), interpolation=cv2.INTER_AREA)
    small_mask = cv2.resize(binary_mask, (inpaint_w, inpaint_h), interpolation=cv2.INTER_LINEAR)

    kernel_size = max(11, int(dilation_radius * scale)) | 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    dilated_small_mask = cv2.dilate(small_mask, kernel, iterations=1)

    # Nếu là ảnh chụp màn hình dọc kiểu TikTok (tỉ lệ h/w > 1.25), làm sạch thêm các icon/text UI ở đáy & cạnh phải
    if clean_social_ui and (h / float(w) > 1.22):
        gray_s = cv2.cvtColor(small_bgr, cv2.COLOR_BGR2GRAY)
        # Phát hiện chữ trắng gắt hoặc nút bấm ở rìa phải (x > 0.86, y in [0.30, 0.96]) và đáy (y > 0.87)
        ui_zone = np.zeros_like(dilated_small_mask)
        ui_zone[int(inpaint_h * 0.87):, :int(inpaint_w * 0.78)] = 255
        right_icons = (gray_s > 235).astype(np.uint8) * 255
        right_mask = np.zeros_like(dilated_small_mask)
        right_mask[int(inpaint_h * 0.30):int(inpaint_h * 0.96), int(inpaint_w * 0.86):] = 255
        right_icons = cv2.bitwise_and(right_icons, right_mask)
        right_icons = cv2.dilate(right_icons, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
        dilated_small_mask = cv2.bitwise_or(dilated_small_mask, right_icons)

    if np.mean(dilated_small_mask > 0) < 0.005:
        return cleaned_border_bgr, False, None

    inpainted_small_bgr = cv2.inpaint(small_bgr, dilated_small_mask, 7, cv2.INPAINT_TELEA)
    inpainted_full_bgr = cv2.resize(inpainted_small_bgr, (w, h), interpolation=cv2.INTER_CUBIC)

    full_mask = cv2.resize(dilated_small_mask, (w, h), interpolation=cv2.INTER_LINEAR)
    fk = max(9, int(19 / scale)) | 1
    feather_mask = cv2.GaussianBlur(full_mask.astype(np.float32) / 255.0, (fk, fk), 0)[..., None]

    cleaned_final = (
        cleaned_border_bgr.astype(np.float32) * (1.0 - feather_mask)
        + inpainted_full_bgr.astype(np.float32) * feather_mask
    )
    return np.clip(cleaned_final, 0, 255).astype(np.uint8), has_person, full_mask


def clean_reference_background(
    bg_image: Image.Image, dilation_radius: int = 25
) -> Tuple[Image.Image, bool, Optional[Image.Image]]:
    """
    Kiểm tra và tự động xóa nhân vật trong ảnh nền mẫu nếu có (nhận & trả về PIL Image).
    """
    img_rgb = np.array(bg_image.convert("RGB"))
    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    cleaned_bgr, has_person, full_mask = clean_reference_background_bgr(img_bgr, dilation_radius=dilation_radius)
    cleaned_rgb = Image.fromarray(cv2.cvtColor(cleaned_bgr, cv2.COLOR_BGR2RGB))
    mask_pil = Image.fromarray(full_mask, mode="L") if full_mask is not None else None
    return cleaned_rgb, has_person, mask_pil
