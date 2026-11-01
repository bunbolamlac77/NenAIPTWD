# File: /Users/phuthanh/APP_CaNhan/NenAI/engine/scene_analyzer.py
"""
NenAI Studio v4.0 - 10/10 Pro Scene Analyzer (CIE LAB & 3D Optics Engine)
- Phân tích bối cảnh trong không gian màu CIE LAB (chuẩn nhận thức thị giác người)
- Tách riêng 3 nguồn ánh sáng: Shadow Tint, Ambient Midtone, Highlight Specular
- Trích xuất Vector nguồn sáng 3D L = (Lx, Ly, Lz) & Đo độ mờ quang học (Bokeh Defocus Sigma)
"""

import cv2
import numpy as np
from typing import Dict, Any, Optional
from sklearn.cluster import MiniBatchKMeans


class SceneAnalyzerV4:
    def __init__(self, n_clusters: int = 5):
        self.n_clusters = n_clusters

    @staticmethod
    def _rgb_to_hex(rgb_tuple) -> str:
        r, g, b = [int(np.clip(c, 0, 255)) for c in rgb_tuple]
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def _bgr_to_hex(bgr_tuple) -> str:
        b, g, r = [int(np.clip(c, 0, 255)) for c in bgr_tuple]
        return f"#{r:02x}{g:02x}{b:02x}"

    def estimate_3d_light_vector(self, bg_rgb: np.ndarray) -> dict:
        """
        Xác định tọa độ nguồn sáng chính (Key Light Vector Lx, Ly, Lz) và màu ánh sáng (Key Light RGB)
        từ 5% điểm ảnh có độ chói cao nhất trên nền.
        """
        small_bg = cv2.resize(bg_rgb, (512, 512), interpolation=cv2.INTER_AREA)
        lab = cv2.cvtColor(small_bg, cv2.COLOR_RGB2LAB).astype(np.float32)
        L_channel = lab[:, :, 0]

        # Lấy top 5% điểm sáng nhất làm nguồn phát sáng
        thresh = np.percentile(L_channel, 95)
        bright_mask = L_channel >= thresh
        y_indices, x_indices = np.where(bright_mask)

        if len(x_indices) > 0:
            weights = L_channel[bright_mask]
            cx = float(np.average(x_indices, weights=weights) / 512.0)  # [0, 1]
            cy = float(np.average(y_indices, weights=weights) / 512.0)  # [0, 1]
            key_light_rgb = np.median(small_bg[bright_mask], axis=0).tolist()
        else:
            cx, cy = 0.5, 0.2
            key_light_rgb = [255, 248, 235]

        # Chuyển sang hệ tọa độ chuẩn hóa [-1, 1] với gốc tại tâm nhân vật (x=0.5, y=0.6)
        lx = float(np.clip((cx - 0.5) * 2.0, -1.0, 1.0))
        ly = float(np.clip((cy - 0.6) * 2.0, -1.0, 1.0))
        # Lz đại diện cho độ chếch của đèn từ phía trước hay ngược sáng (Backlight)
        backlight_ratio = float(np.mean(L_channel[100:400, 150:360]) / (np.mean(L_channel) + 1e-5))
        lz = float(np.clip(0.85 - (backlight_ratio - 1.0) * 0.5, 0.25, 0.95))

        norm = np.sqrt(lx**2 + ly**2 + lz**2 + 1e-6)
        return {
            "vector_xyz": (round(float(lx / norm), 3), round(float(ly / norm), 3), round(float(lz / norm), 3)),
            "light_source_uv": (round(cx, 3), round(cy, 3)),
            "key_light_rgb": [int(c) for c in key_light_rgb],
            "key_light_hex": self._rgb_to_hex(key_light_rgb)
        }

    def analyze_floor_and_defocus(self, bg_rgb: np.ndarray, standing_y_ratio: float = 0.85) -> dict:
        """
        Đo độ phản xạ sàn (Reflectivity) và độ mờ ống kính (Optical Bokeh Sigma) tại vị trí chân đứng.
        """
        h, w, _ = bg_rgb.shape
        floor_y0 = int(h * max(0.70, standing_y_ratio - 0.08))
        floor_patch = bg_rgb[floor_y0:h, int(w * 0.2):int(w * 0.8)]
        floor_gray = cv2.cvtColor(floor_patch, cv2.COLOR_RGB2GRAY)

        # Phương sai Laplacian đo độ sắc nét tại mặt sàn để đồng bộ độ mờ gấu váy
        laplacian_var = float(cv2.Laplacian(floor_gray, cv2.CV_64F).var())
        # Quy đổi ra bán kính làm mờ (sigma) cho gấu váy phía sau
        recommended_hem_blur_sigma = float(np.clip(18.0 / (np.sqrt(laplacian_var) + 2.0), 0.0, 4.5))

        # Độ phản xạ sàn dựa trên độ bóng Specular và độ mượt bề mặt
        specular_ratio = float(np.percentile(floor_gray, 95) - np.percentile(floor_gray, 50)) / 255.0
        floor_reflectivity = float(np.clip(specular_ratio * 1.4, 0.05, 0.85))

        return {
            "floor_reflectivity": round(floor_reflectivity, 3),
            "floor_laplacian_sharpness": round(laplacian_var, 2),
            "hem_defocus_sigma": round(recommended_hem_blur_sigma, 2)
        }

    def analyze_scene(self, bg_rgb: np.ndarray, standing_y_ratio: float = 0.85) -> dict:
        """
        Phân tích toàn diện bối cảnh trong không gian màu CIE LAB.
        """
        small = cv2.resize(bg_rgb, (256, 256), interpolation=cv2.INTER_AREA)
        lab_pixels = cv2.cvtColor(small, cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)

        kmeans = MiniBatchKMeans(n_clusters=self.n_clusters, random_state=42, batch_size=2048, n_init="auto")
        kmeans.fit(lab_pixels)

        centers_lab = kmeans.cluster_centers_.astype(np.uint8).reshape(1, -1, 3)
        centers_rgb = cv2.cvtColor(centers_lab, cv2.COLOR_LAB2RGB).reshape(-1, 3)

        # Sắp xếp các cụm màu theo độ sáng L tăng dần: Cụm tối nhất -> Màu bóng đổ, Cụm giữa -> Ambient, Cụm sáng -> Highlight
        luminance_order = np.argsort(centers_lab[0, :, 0])
        sorted_rgb = centers_rgb[luminance_order]

        shadow_rgb = sorted_rgb[0].tolist()
        ambient_rgb = sorted_rgb[len(sorted_rgb) // 2].tolist()
        highlight_rgb = sorted_rgb[-1].tolist()

        light_info = self.estimate_3d_light_vector(bg_rgb)
        floor_info = self.analyze_floor_and_defocus(bg_rgb, standing_y_ratio)

        return {
            "palette_hex": [self._rgb_to_hex(c) for c in sorted_rgb],
            "shadow_tint_rgb": [int(c) for c in shadow_rgb],
            "shadow_tint_hex": self._rgb_to_hex(shadow_rgb),
            "ambient_midtone_rgb": [int(c) for c in ambient_rgb],
            "ambient_midtone_hex": self._rgb_to_hex(ambient_rgb),
            "highlight_rgb": [int(c) for c in highlight_rgb],
            "highlight_hex": self._rgb_to_hex(highlight_rgb),
            "lighting_3d": light_info,
            "optics_and_floor": floor_info
        }

    # =========================================================================
    # BACKWARD COMPATIBILITY HELPERS
    # =========================================================================
    def analyze_reference_scene(self, ref_bgr: np.ndarray) -> Dict[str, Any]:
        """Tương thích ngược với hệ thống Preset & UI hiện tại."""
        ref_rgb = cv2.cvtColor(ref_bgr, cv2.COLOR_BGR2RGB)
        scene_meta = self.analyze_scene(ref_rgb)
        
        # Bổ sung các trường dữ liệu cho UI / Panel
        color_palette = [
            {"hex": h, "name": f"Color {i+1}"}
            for i, h in enumerate(scene_meta["palette_hex"])
        ]
        breakdown = {
            "background": {"hex": scene_meta["ambient_midtone_hex"], "desc": "Màu phông tường chính"},
            "floor": {"hex": scene_meta["shadow_tint_hex"], "desc": "Mặt sàn & màu bóng đổ"},
            "lighting": {"hex": scene_meta["highlight_hex"], "desc": "Nguồn sáng chính Key Light"},
        }

        lx, ly, _ = scene_meta["lighting_3d"]["vector_xyz"]
        light_dir = "left" if lx < -0.1 else ("right" if lx > 0.1 else "center")

        return {
            "color_palette": color_palette,
            "palette_hex": scene_meta["palette_hex"],
            "breakdown": breakdown,
            "lighting_style": "studio_3d",
            "light_direction": light_dir,
            "y_horizon": 0.85,
            "lighting_3d": scene_meta["lighting_3d"],
            "optics_and_floor": scene_meta["optics_and_floor"],
            "shadow_tint_rgb": scene_meta["shadow_tint_rgb"],
            "ambient_midtone_rgb": scene_meta["ambient_midtone_rgb"],
            "highlight_rgb": scene_meta["highlight_rgb"],
        }

    def compute_dress_flanking_zones(self, alpha_core: np.ndarray) -> Dict[str, Any]:
        """Tính toán tỉ lệ mở rộng tà váy cho Prompt thiết kế."""
        h, w = alpha_core.shape[:2]
        y_bottom = int(h * 0.85)
        bottom_row = alpha_core[y_bottom, :] > 0.3
        nz = np.where(bottom_row)[0]
        dress_width = (nz[-1] - nz[0]) / w if len(nz) > 0 else 0.5
        return {
            "dress_width_ratio": round(float(dress_width), 2),
            "left_flank_px": int(nz[0]) if len(nz) > 0 else 0,
            "right_flank_px": int(nz[-1]) if len(nz) > 0 else w,
        }

    def build_silhouette_aware_prompt(self, scene_info: Dict[str, Any], flanking_info: Optional[Dict[str, Any]] = None) -> str:
        light_info = scene_info.get("lighting_3d", {})
        dir_name = scene_info.get("light_direction", "studio")
        return f"A high-end luxury Korean wedding studio background with soft floral arch, directional lighting from {dir_name}, elegant floor reflections, cinematic bokeh."

    @classmethod
    def is_same_subject_ai_composite(cls, img1: np.ndarray, img2: np.ndarray) -> bool:
        """Kiểm tra xem 2 ảnh có cùng góc chụp nhân vật không."""
        try:
            h1, w1 = img1.shape[:2]
            h2, w2 = img2.shape[:2]
            s1 = cv2.resize(img1, (256, 256))
            s2 = cv2.resize(img2, (256, 256))
            diff = np.mean(np.abs(s1.astype(float) - s2.astype(float)))
            return diff < 85.0
        except Exception:
            return True


# =========================================================================
# SINGLETONS & ALIASES
# =========================================================================
SceneAnalyzer = SceneAnalyzerV4
SceneAnalyzerV3 = SceneAnalyzerV4

def analyze_and_describe_scene(img, user_prompt=""):
    analyzer = SceneAnalyzerV4()
    if img.ndim == 3 and img.shape[2] == 3:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    else:
        rgb = img
    return analyzer.analyze_scene(rgb)
