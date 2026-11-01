# File: /Users/phuthanh/APP_CaNhan/NenAI/engine/harmonizer.py
"""
NenAI Studio v4.0 - 10/10 Pro Wedding Harmonizer (Physics-Guided Optical Compositor)
- Dual-Mask Protection: Bảo vệ kép Da mặt (YCrCb) + Ren trắng váy cưới (High-L Low-Chroma)
- 2.5D Relighting & Fresnel Rim Light: Khối ánh sáng 3D theo vector L + viền sáng ven tóc/voan
- Dual-Physical Shadow: Contact AO (chân/gấu váy) + Variable-Blur Cast Shadow (nhòe theo khoảng cách)
- Multi-Scale Exponential Light Wrap: Ánh sáng nền tràn tự nhiên qua viền voan & tóc tơ
"""

import os
import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

from engine.matting import MattingEngineV4, get_matting_engine
from engine.scene_analyzer import SceneAnalyzerV4


class HarmonizerV4:
    def __init__(self, output_dir: str = "/Users/phuthanh/APP_CaNhan/NenAI/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.matting = get_matting_engine()
        self.analyzer = SceneAnalyzerV4()

    def build_protection_masks(self, fg_rgb: np.ndarray, alpha_mask: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Tạo 2 mặt nạ bảo vệ chuyên biệt cho ảnh cưới:
        1. skin_mask: Bảo vệ da mặt và lớp trang điểm cô dâu trong không gian YCrCb.
        2. dress_highlight_mask: Bảo vệ chi tiết ren trắng vùng sáng của váy cưới không bị ám đục.
        """
        ycrcb = cv2.cvtColor(fg_rgb, cv2.COLOR_RGB2YCrCb)
        # Khoảng màu da người châu Á dưới ánh sáng studio
        skin_raw = cv2.inRange(ycrcb, np.array([45, 132, 75]), np.array([245, 175, 128])).astype(np.float32) / 255.0
        skin_mask = cv2.GaussianBlur(skin_raw * alpha_mask, (31, 31), 0)

        # Phát hiện vùng ren trắng sáng của váy cưới (Luminance cao, độ bão hòa màu thấp)
        lab = cv2.cvtColor(fg_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
        L_norm = lab[:, :, 0] / 255.0
        chroma = np.sqrt((lab[:, :, 1] - 128.0)**2 + (lab[:, :, 2] - 128.0)**2)
        dress_white = ((L_norm > 0.72) & (chroma < 14.0)).astype(np.float32) * (1.0 - skin_mask)
        dress_highlight_mask = cv2.GaussianBlur(dress_white * alpha_mask, (21, 21), 0)

        return np.clip(skin_mask, 0.0, 1.0), np.clip(dress_highlight_mask, 0.0, 1.0)

    def harmonize_subject_color(
        self,
        fg_rgb: np.ndarray,
        bg_rgb: np.ndarray,
        alpha_mask: np.ndarray,
        strength: float = 0.55
    ) -> np.ndarray:
        """
        Chuyển đổi màu sắc thống kê Reinhard trong không gian CIE LAB nhưng giữ nguyên tần số chi tiết
        và bảo vệ tuyệt đối da mặt (85%) + vùng sáng váy cưới (75%).
        """
        skin_mask, dress_highlight_mask = self.build_protection_masks(fg_rgb, alpha_mask)

        fg_lab = cv2.cvtColor(fg_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
        bg_lab = cv2.cvtColor(bg_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)

        valid = alpha_mask > 0.5
        if not np.any(valid):
            return fg_rgb

        out_lab = fg_lab.copy()
        # Chỉ dịch chuyển nhẹ kênh L (30%) để giữ micro-contrast gốc, dịch chuyển kênh A/B theo môi trường
        channel_weights = [0.28 * strength, 0.65 * strength, 0.65 * strength]

        for c in range(3):
            fg_mean, fg_std = np.mean(fg_lab[:, :, c][valid]), np.std(fg_lab[:, :, c][valid]) + 1e-5
            bg_mean, bg_std = np.mean(bg_lab[:, :, c]), np.std(bg_lab[:, :, c]) + 1e-5

            # Giới hạn hệ số co giãn độ tương phản trong đoạn [0.82, 1.18] để không làm cháy váy hoặc bệt tóc
            scale_ratio = np.clip(bg_std / fg_std, 0.82, 1.18)
            transferred = (fg_lab[:, :, c] - fg_mean) * scale_ratio + bg_mean

            w = channel_weights[c]
            out_lab[:, :, c] = fg_lab[:, :, c] * (1.0 - w) + transferred * w

        # Áp mặt nạ bảo vệ da mặt (giữ 85% màu da gốc) và bảo vệ ren trắng váy cưới (giữ 75% độ trắng tinh khiết)
        protection = np.clip(skin_mask * 0.85 + dress_highlight_mask * 0.75, 0.0, 0.92)[..., None]
        final_lab = out_lab * (1.0 - protection) + fg_lab * protection
        final_lab = np.clip(final_lab, 0, 255).astype(np.uint8)

        return cv2.cvtColor(final_lab, cv2.COLOR_LAB2RGB)

    def generate_25d_relight_and_rim_layer(
        self,
        fg_rgb: np.ndarray,
        alpha_mask: np.ndarray,
        light_vector_xyz: tuple = (0.4, -0.5, 0.75),
        key_light_rgb: list = [255, 244, 228]
    ) -> np.ndarray:
        """
        Tạo Layer 'Relight & Rim Light' (RGBA) dựa trên vector pháp tuyến bề mặt 2.5D và hiệu ứng Fresnel ở viền tóc/voan.
        """
        h, w = alpha_mask.shape
        # Xây dựng trường độ cao giả lập (Pseudo-Depth) từ khoảng cách biên kết hợp độ sáng nội tại
        binary_mask = (alpha_mask > 0.15).astype(np.uint8)
        dist_field = cv2.distanceTransform(binary_mask, cv2.DIST_L2, 5).astype(np.float32)
        max_dist = np.max(dist_field) + 1e-5
        norm_dist = cv2.GaussianBlur(dist_field / max_dist, (31, 31), 0)

        gray = cv2.cvtColor(fg_rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
        pseudo_depth = norm_dist * 0.7 + cv2.GaussianBlur(gray, (15, 15), 0) * 0.3

        # Đạo hàm không gian tìm Vector Pháp tuyến bề mặt N = (-dz/dx, -dz/dy, 1)
        nx = -cv2.Sobel(pseudo_depth, cv2.CV_32F, 1, 0, ksize=5) * 3.5
        ny = -cv2.Sobel(pseudo_depth, cv2.CV_32F, 0, 1, ksize=5) * 3.5
        nz = np.ones_like(pseudo_depth)
        norm = np.sqrt(nx**2 + ny**2 + nz**2 + 1e-6)
        nx, ny, nz = nx / norm, ny / norm, nz / norm

        lx, ly, lz = light_vector_xyz
        # 1. Ánh sáng khối Lambertian (N . L)
        diffuse = np.clip(nx * lx + ny * ly + nz * lz, 0.0, 1.0)

        # 2. Ánh sáng ven Fresnel Rim Light (tập trung ở biên tóc, vai và voan phía đón nắng)
        edge_zone = np.exp(-dist_field / 18.0) * (alpha_mask > 0.02)
        directional_rim = np.clip(nx * lx + ny * ly, 0.0, 1.0)
        rim_intensity = edge_zone * (0.35 + 0.65 * directional_rim)

        total_light_alpha = np.clip((diffuse * 0.35 + rim_intensity * 0.85) * alpha_mask, 0.0, 1.0)

        relight_rgba = np.zeros((h, w, 4), dtype=np.uint8)
        for c in range(3):
            relight_rgba[:, :, c] = int(np.clip(key_light_rgb[c], 0, 255))
        relight_rgba[:, :, 3] = (total_light_alpha * 255.0).astype(np.uint8)
        return relight_rgba

    def generate_multiscale_light_wrap(
        self,
        bg_rgb: np.ndarray,
        alpha_mask: np.ndarray,
        radii: list = [8, 24, 64]
    ) -> np.ndarray:
        """
        Tạo Layer 'Light Wrap Quang Học' (RGBA) theo hàm mũ đa tỷ lệ, giúp nền ánh sáng tràn tự nhiên qua voan & tóc.
        """
        h, w = alpha_mask.shape
        inv_alpha = 1.0 - alpha_mask
        wrap_accum = np.zeros((h, w, 3), dtype=np.float32)
        mask_accum = np.zeros((h, w), dtype=np.float32)

        bg_float = bg_rgb.astype(np.float32) / 255.0
        weights = [0.5, 0.3, 0.2]

        for r, weight in zip(radii, weights):
            ksize = r * 2 + 1
            blurred_bg = cv2.GaussianBlur(bg_float, (ksize, ksize), r * 0.5)
            blurred_inv_alpha = cv2.GaussianBlur(inv_alpha, (ksize, ksize), r * 0.5)
            spill = blurred_inv_alpha * alpha_mask
            wrap_accum += blurred_bg * spill[..., None] * weight
            mask_accum += spill * weight

        mask_accum = np.clip(mask_accum * 2.2, 0.0, 1.0)
        safe_div = np.maximum(mask_accum[..., None], 1e-4)
        wrap_rgb = np.clip(wrap_accum / safe_div, 0.0, 1.0)

        light_wrap_rgba = np.zeros((h, w, 4), dtype=np.uint8)
        light_wrap_rgba[:, :, :3] = (wrap_rgb * 255.0).astype(np.uint8)
        light_wrap_rgba[:, :, 3] = (mask_accum * 255.0).astype(np.uint8)
        return light_wrap_rgba

    def generate_dual_physical_shadow(
        self,
        alpha_mask: np.ndarray,
        light_vector_xyz: tuple = (0.4, -0.5, 0.75),
        shadow_tint_rgb: list = [28, 24, 32],
        floor_reflectivity: float = 0.25
    ) -> np.ndarray:
        """
        Tạo Layer 'Bóng Vật Lý Kép' (RGBA) gồm:
        1. Contact Shadow (AO): Bóng đậm và sắc nét ngay khe tiếp xúc giữa đế giày/gấu váy và mặt sàn.
        2. Variable-Blur Cast Shadow: Bóng đổ phóng chiếu theo góc nguồn sáng, càng xa chân càng nhòe rộng và mờ dần.
        """
        h, w = alpha_mask.shape
        y_indices, x_indices = np.where(alpha_mask > 0.5)
        if len(y_indices) == 0:
            return np.zeros((h, w, 4), dtype=np.uint8)

        foot_y = int(np.percentile(y_indices, 99.2))
        top_y = int(np.min(y_indices))
        subj_height = max(100, foot_y - top_y)

        # --- PHẦN 1: Contact Shadow (Ambient Occlusion tại điểm chạm đất) ---
        contact_zone_h = max(12, int(subj_height * 0.035))
        contact_mask = np.zeros((h, w), dtype=np.float32)
        y0_c = max(0, foot_y - contact_zone_h)
        y1_c = min(h, foot_y + int(contact_zone_h * 0.6))
        contact_mask[y0_c:y1_c, :] = alpha_mask[y0_c:y1_c, :]
        # Kéo ngang nhẹ và làm mềm dọc để tạo khe tối dưới gấu váy/đế giày
        contact_shadow = cv2.GaussianBlur(contact_mask, (35, 11), 0)
        contact_shadow = np.clip(contact_shadow * 0.88, 0.0, 0.88)

        # --- PHẦN 2: Perspective Cast Shadow với độ nhòe biến thiên (Variable Blur) ---
        lx, ly, lz = light_vector_xyz
        # Hướng bóng đổ ngược với hướng nguồn sáng
        skew_x = -lx / max(lz, 0.3) * 0.45
        scale_y = float(np.clip(0.28 + abs(ly) * 0.25, 0.20, 0.55))

        # Ma trận biến đổi phối cảnh mặt phẳng sàn quanh trục ngang tại vị trí chân (foot_y)
        M = np.array([
            [1.0, skew_x, -skew_x * foot_y],
            [0.0, scale_y, foot_y * (1.0 - scale_y)]
        ], dtype=np.float32)

        projected_mask = cv2.warpAffine(alpha_mask, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

        # Tạo ngân hàng 4 cấp độ làm mờ (Multi-Stop Blur Bank) và nội suy theo khoảng cách tới chân
        b1 = cv2.GaussianBlur(projected_mask, (11, 11), 3)
        b2 = cv2.GaussianBlur(projected_mask, (35, 35), 12)
        b3 = cv2.GaussianBlur(projected_mask, (81, 81), 28)
        b4 = cv2.GaussianBlur(projected_mask, (151, 151), 55)

        y_grid = np.arange(h, dtype=np.float32)[:, None]
        dist_from_feet = np.clip(np.abs(y_grid - foot_y) / (subj_height * scale_y + 1e-5), 0.0, 1.0)

        # Nội suy mượt giữa các cấp độ mờ: sát chân -> b1, xa chân -> b4
        cast_shadow = (
            b1 * np.clip(1.0 - dist_from_feet * 3.0, 0.0, 1.0) +
            b2 * np.clip(1.0 - np.abs(dist_from_feet - 0.33) * 3.0, 0.0, 1.0) +
            b3 * np.clip(1.0 - np.abs(dist_from_feet - 0.66) * 3.0, 0.0, 1.0) +
            b4 * np.clip((dist_from_feet - 0.66) * 3.0, 0.0, 1.0)
        )
        # Giảm dần độ đậm theo khoảng cách và độ phản xạ sàn
        falloff = np.exp(-dist_from_feet * 1.8) * (0.55 * (1.0 - floor_reflectivity * 0.4))
        cast_shadow = np.clip(cast_shadow * falloff, 0.0, 0.65)

        # Kết hợp Contact AO + Cast Shadow (loại trừ phần bóng đè lên chính thân trên nhân vật)
        combined_shadow_alpha = np.maximum(contact_shadow, cast_shadow * (1.0 - alpha_mask * 0.85))
        combined_shadow_alpha = np.clip(combined_shadow_alpha, 0.0, 0.90)

        shadow_rgba = np.zeros((h, w, 4), dtype=np.uint8)
        for c in range(3):
            # Pha màu bóng theo tông tối thực tế của sàn nền (Shadow Tint)
            shadow_rgba[:, :, c] = int(np.clip(shadow_tint_rgb[c] * 0.6, 0, 90))
        shadow_rgba[:, :, 3] = (combined_shadow_alpha * 255.0).astype(np.uint8)
        return shadow_rgba

    # =========================================================================
    # QUY TRÌNH TOÀN TRÌNH MASTER PIPELINE V4 (10/10)
    # =========================================================================
    def process_master_pipeline(
        self,
        subject_bgr_33mp: np.ndarray,
        reference_or_ai_bgr: Optional[np.ndarray] = None,
        is_ai_composite: bool = True,
        job_id: str = "master_job",
        shot_type: str = "full_body",
        skin_shield_enabled: bool = True,
        passe_partout: str = "none",
        lighting_style: str = "natural",
        harmonize_strength: float = 0.55,
        veil_gamma: float = 1.18,
    ) -> Dict[str, str]:
        """
        Quy trình xử lý hoàn chỉnh chuẩn 10/10:
        1. Tách nền bằng BiRefNet + Unmixing + Veil Gamma Curve (Sạch 100% sương trắng).
        2. Phân tích bối cảnh CIE LAB 3D (Key Light Vector, Shadow Tint, Floor Refl).
        3. Hòa trộn màu sắc Dual-Mask Protection (Da mặt + Ren trắng váy cưới).
        4. Tạo 2.5D Relight & Rim Light Layer.
        5. Tạo Multi-Scale Exponential Light Wrap Layer.
        6. Tạo Dual-Physical Shadow (Contact AO + Cast Shadow).
        7. Xuất toàn bộ file layer ra đĩa và ghép ảnh Master Preview sắc nét.
        """
        fg_rgb = cv2.cvtColor(subject_bgr_33mp, cv2.COLOR_BGR2RGB)
        h, w = fg_rgb.shape[:2]

        # 1. Chuẩn bị ảnh nền
        if reference_or_ai_bgr is not None:
            bg_bgr = cv2.resize(reference_or_ai_bgr, (w, h), interpolation=cv2.INTER_CUBIC)
            bg_rgb = cv2.cvtColor(bg_bgr, cv2.COLOR_BGR2RGB)
        else:
            bg_rgb = np.full((h, w, 3), 245, dtype=np.uint8)

        # 2. Tách nền & Khử mù trắng voan cưới
        raw_alpha = self.matting.predict_raw_alpha(fg_rgb)
        clean_fg_rgb, refined_alpha = self.matting.unmix_and_refine_veil(
            fg_rgb, raw_alpha, veil_gamma=veil_gamma
        )

        # 3. Phân tích bối cảnh CIE LAB
        scene_meta = self.analyzer.analyze_scene(bg_rgb)
        light_vec = scene_meta["lighting_3d"]["vector_xyz"]
        key_light_rgb = scene_meta["lighting_3d"]["key_light_rgb"]
        shadow_tint_rgb = scene_meta["shadow_tint_rgb"]
        floor_refl = scene_meta["optics_and_floor"]["floor_reflectivity"]

        # Điều chỉnh vector nếu chọn phong cách ánh sáng khác
        if lighting_style == "rim_light":
            light_vec = (light_vec[0] * 1.2, light_vec[1], 0.35)
        elif lighting_style == "dreamy":
            harmonize_strength = max(0.40, harmonize_strength * 0.8)

        # 4. Hòa trộn màu sắc & Bảo vệ kép da mặt + ren trắng
        harmonized_fg_rgb = self.harmonize_subject_color(
            clean_fg_rgb, bg_rgb, refined_alpha, strength=harmonize_strength
        )

        # 5. Tạo các Layer quang học
        relight_rgba = self.generate_25d_relight_and_rim_layer(
            harmonized_fg_rgb, refined_alpha, light_vec, key_light_rgb
        )
        light_wrap_rgba = self.generate_multiscale_light_wrap(bg_rgb, refined_alpha)
        shadow_rgba = self.generate_dual_physical_shadow(
            refined_alpha, light_vec, shadow_tint_rgb, floor_refl
        )

        # 6. Tạo ảnh gộp Master Preview
        bg_float = bg_rgb.astype(np.float32) / 255.0
        sh_alpha = (shadow_rgba[:, :, 3].astype(np.float32) / 255.0)[..., None]
        sh_rgb = (shadow_rgba[:, :, :3].astype(np.float32) / 255.0)
        # Apply shadow multiply
        comp = bg_float * (1.0 - sh_alpha) + (bg_float * sh_rgb * 1.5) * sh_alpha

        # Overlay Subject
        fg_a = refined_alpha[..., None]
        comp = comp * (1.0 - fg_a) + (harmonized_fg_rgb.astype(np.float32) / 255.0) * fg_a

        # Overlay Relight (Soft Light blend)
        rl_a = (relight_rgba[:, :, 3].astype(np.float32) / 255.0)[..., None]
        rl_rgb = relight_rgba[:, :, :3].astype(np.float32) / 255.0
        soft_blend = 2 * comp * rl_rgb + comp * comp * (1.0 - 2 * rl_rgb)
        comp = comp * (1.0 - rl_a * 0.65) + soft_blend * (rl_a * 0.65)

        # Overlay Light Wrap (Screen blend)
        lw_a = (light_wrap_rgba[:, :, 3].astype(np.float32) / 255.0)[..., None]
        lw_rgb = light_wrap_rgba[:, :, :3].astype(np.float32) / 255.0
        screen_blend = 1.0 - (1.0 - comp) * (1.0 - lw_rgb)
        comp = comp * (1.0 - lw_a * 0.60) + screen_blend * (lw_a * 0.60)

        master_rgb = (np.clip(comp, 0.0, 1.0) * 255.0).astype(np.uint8)

        # 7. Xuất file đĩa
        p_master = str(self.output_dir / f"{job_id}_master.jpg")
        p_bg = str(self.output_dir / f"{job_id}_07_bg.png")
        p_shadow = str(self.output_dir / f"{job_id}_06_shadow.png")
        p_subj_rgb = str(self.output_dir / f"{job_id}_05_subject_rgb.png")
        p_subj_alpha = str(self.output_dir / f"{job_id}_05_subject_alpha.png")
        p_relight = str(self.output_dir / f"{job_id}_04_relight.png")
        p_wrap = str(self.output_dir / f"{job_id}_03_light_wrap.png")
        p_cutout = str(self.output_dir / f"{job_id}_cutout.png")

        # Lưu ảnh JPG Master Preview
        cv2.imwrite(p_master, cv2.cvtColor(master_rgb, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])
        cv2.imwrite(p_bg, cv2.cvtColor(bg_rgb, cv2.COLOR_RGB2BGR))
        cv2.imwrite(p_shadow, cv2.cvtColor(shadow_rgba, cv2.COLOR_RGBA2BGRA))
        cv2.imwrite(p_subj_rgb, cv2.cvtColor(harmonized_fg_rgb, cv2.COLOR_RGB2BGR))
        cv2.imwrite(p_subj_alpha, (refined_alpha * 255.0).astype(np.uint8))
        cv2.imwrite(p_relight, cv2.cvtColor(relight_rgba, cv2.COLOR_RGBA2BGRA))
        cv2.imwrite(p_wrap, cv2.cvtColor(light_wrap_rgba, cv2.COLOR_RGBA2BGRA))

        # Lưu thêm file Cutout RGBA truyền thống cho các công cụ khác
        cutout_rgba = np.zeros((h, w, 4), dtype=np.uint8)
        cutout_rgba[:, :, :3] = cv2.cvtColor(harmonized_fg_rgb, cv2.COLOR_RGB2BGR)
        cutout_rgba[:, :, 3] = (refined_alpha * 255.0).astype(np.uint8)
        cv2.imwrite(p_cutout, cutout_rgba)

        return {
            "master_path": p_master,
            "07_background": p_bg,
            "06_shadow": p_shadow,
            "05_subject_rgb": p_subj_rgb,
            "05_subject_alpha": p_subj_alpha,
            "04_relight": p_relight,
            "03_light_wrap": p_wrap,
            "02_atmosphere": "",
            "01_foreground": "",
            # Backward compatibility keys for existing UXP Panel
            "layer1_floral_fg": "",
            "layer2_subject_33mp": p_cutout,
            "layer3_light_wrap": p_wrap,
            "layer4_real_shadow": p_shadow,
            "layer5_clean_bg": p_bg,
        }


# =========================================================================
# SINGLETONS & ALIASES
# =========================================================================
Harmonizer = HarmonizerV4
HarmonizerMaster = HarmonizerV4
HarmonizerMasterV3 = HarmonizerV4

def harmonize_studio_master(
    subject_bgr: np.ndarray,
    reference_bgr: Optional[np.ndarray] = None,
    output_dir: str = "/Users/phuthanh/APP_CaNhan/NenAI/output",
    job_id: str = "master",
    **kwargs
) -> Dict[str, str]:
    engine = HarmonizerV4(output_dir=output_dir)
    return engine.process_master_pipeline(
        subject_bgr_33mp=subject_bgr,
        reference_or_ai_bgr=reference_bgr,
        job_id=job_id,
        **kwargs
    )
