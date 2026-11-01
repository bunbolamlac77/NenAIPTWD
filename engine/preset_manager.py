"""
Module Quản Lý Kho Bối Cảnh Studio (Preset & Template Vault v4.0)
Lưu trữ và tái sử dụng các mẫu bối cảnh đã làm sạch
"""

import os
import re
import json
import uuid
import shutil
from pathlib import Path
from typing import Union, Optional
import cv2
import numpy as np
from PIL import Image

PRESETS_DIR = Path("/Users/phuthanh/APP_CaNhan/NenAI/presets")
PRESETS_DIR.mkdir(parents=True, exist_ok=True)


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", text.strip().lower()).strip("_")
    return slug or f"preset_{uuid.uuid4().hex[:6]}"


def list_presets() -> list[dict]:
    """
    Lấy danh sách toàn bộ các bối cảnh mẫu trong kho.
    """
    presets = []
    if not PRESETS_DIR.exists():
        return presets

    for p_dir in sorted(PRESETS_DIR.iterdir()):
        if p_dir.is_dir():
            meta_file = p_dir / "meta.json"
            clean_bg = p_dir / "clean_bg.jpg"
            thumb_file = p_dir / "thumb.jpg"

            if meta_file.exists() and clean_bg.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    meta["id"] = meta.get("id", p_dir.name)
                    meta["name"] = meta.get("name", meta.get("title", p_dir.name))
                    meta["title"] = meta.get("title", meta["name"])
                    meta["clean_bg_url"] = f"/presets/{p_dir.name}/clean_bg.jpg"
                    meta["thumb_url"] = f"/presets/{p_dir.name}/thumb.jpg" if thumb_file.exists() else meta["clean_bg_url"]
                    meta["preview"] = meta.get("preview", meta["clean_bg_url"])
                    meta["floorHex"] = meta.get("floorHex") or meta.get("floor_hex") or "#E2D5C1"
                    meta["wallHex"] = meta.get("wallHex") or meta.get("wall_hex") or "#EFE5D4"
                    meta["flowerHex"] = meta.get("flowerHex") or meta.get("flower_hex") or "#F7F2E7"
                    meta["tag"] = meta.get("tag") or meta.get("category", "STUDIO").upper()
                    meta["sub"] = meta.get("sub") or meta.get("tone") or f"Hướng sáng {meta.get('light_dir', 'tự nhiên')}"
                    meta["fg"] = meta.get("fg") or "Mặt sàn tiếp đất tự nhiên kèm bóng đổ 3D."
                    meta["mid"] = meta.get("mid") or "Độ nét chủ thể 33MP sắc nét, bảo vệ da và trang phục cưới."
                    meta["bg"] = meta.get("bg") or "Phông nền bối cảnh được tối ưu hòa sắc quang học."
                    presets.append(meta)
                except Exception as e:
                    print(f"[Preset Manager] Lỗi đọc {meta_file}: {e}")

    return presets


def save_preset(
    preset_id_or_name: str,
    name_or_image: Union[str, Path, Image.Image, np.ndarray],
    category: str = "Studio",
    clean_bg_img: Optional[Union[Image.Image, np.ndarray, str, Path]] = None,
    light_dir: str = "left",
    prompt_en: str = "",
) -> dict:
    """
    Lưu một bối cảnh đã làm sạch vào kho mẫu.
    Hỗ trợ linh hoạt cả 2 kiểu gọi:
    - save_preset(name, image_path, category="Studio", light_dir="left")
    - save_preset(preset_id, name, category, clean_bg_img, light_dir="left", prompt_en="")
    """
    if clean_bg_img is None:
        # Kiểu gọi rút gọn: save_preset(name, image_or_path, category=..., light_dir=...)
        name = preset_id_or_name
        preset_id = f"{_slugify(name)}_{uuid.uuid4().hex[:4]}"
        img_source = name_or_image
    else:
        preset_id = preset_id_or_name
        name = str(name_or_image)
        img_source = clean_bg_img

    if isinstance(img_source, (str, Path)):
        pil_img = Image.open(str(img_source)).convert("RGB")
    elif isinstance(img_source, np.ndarray):
        pil_img = Image.fromarray(cv2.cvtColor(img_source, cv2.COLOR_BGR2RGB))
    elif isinstance(img_source, Image.Image):
        pil_img = img_source.convert("RGB")
    else:
        raise ValueError("Nguồn ảnh preset không hợp lệ.")

    target_dir = PRESETS_DIR / preset_id
    target_dir.mkdir(parents=True, exist_ok=True)

    clean_bg_path = target_dir / "clean_bg.jpg"
    thumb_path = target_dir / "thumb.jpg"

    pil_img.save(clean_bg_path, quality=96)

    thumb = pil_img.resize((300, 400), Image.LANCZOS)
    thumb.save(thumb_path, quality=88)

    meta = {
        "id": preset_id,
        "name": name,
        "title": name,
        "category": category,
        "tag": category.upper(),
        "sub": f"Hướng sáng {light_dir}",
        "light_dir": light_dir,
        "prompt_en": prompt_en,
        "width": pil_img.size[0],
        "height": pil_img.size[1],
        "floorHex": "#E2D5C1",
        "wallHex": "#EFE5D4",
        "flowerHex": "#F7F2E7",
        "fg": "Mặt sàn tiếp đất tự nhiên kèm bóng đổ 3D.",
        "mid": "Khóa cứng 100% độ nét pixel gốc Dâu Rể 33MP (Zero-Halo).",
        "bg": "Bối cảnh chuẩn Studio hòa sắc quang học toàn diện.",
    }

    try:
        from engine.scene_analyzer import SceneAnalyzerV3
        analyzer = SceneAnalyzerV3()
        np_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        scene_info = analyzer.analyze_reference_scene(np_bgr)
        cp = scene_info.get("color_palette", {})
        bd = scene_info.get("breakdown", {})
        if cp.get("floor_hex"):
            meta["floorHex"] = cp["floor_hex"]
        if cp.get("wall_hex"):
            meta["wallHex"] = cp["wall_hex"]
        if cp.get("flower_hex"):
            meta["flowerHex"] = cp["flower_hex"]

        if bd.get("tien_canh"):
            meta["fg"] = f"{bd['tien_canh'].get('mat_san', '')} {bd['tien_canh'].get('cum_hoa_sat_san', '')}".strip()
        if bd.get("trung_canh"):
            meta["mid"] = f"{bd['trung_canh'].get('vom_hoa', '')} {bd['trung_canh'].get('khoang_trong_nhan_vat', '')}".strip()
        if bd.get("hau_canh_va_nen"):
            meta["bg"] = f"{bd['hau_canh_va_nen'].get('tuong_nen', '')} {bd['hau_canh_va_nen'].get('anh_sang', '')}".strip()
    except Exception as e:
        print(f"[Preset Manager] Không thể phân tích màu sắc preset: {e}")

    with open(target_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    meta["clean_bg_url"] = f"/presets/{preset_id}/clean_bg.jpg"
    meta["thumb_url"] = f"/presets/{preset_id}/thumb.jpg"
    meta["preview"] = meta["clean_bg_url"]
    return meta


def delete_preset(preset_id: str) -> bool:
    target_dir = PRESETS_DIR / preset_id
    if target_dir.exists() and target_dir.is_dir():
        shutil.rmtree(target_dir)
        return True
    return False
