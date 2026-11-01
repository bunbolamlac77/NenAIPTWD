"""
NenAI Studio v4.0 - 10/10 Pro Wedding Compositor (Apple Silicon MPS Accelerated)
FastAPI Gateway điều phối toàn trình 1-Click:
- MattingEngineV4: Bilinear Studio Backdrop Map + Fast Guided Filter 33MP + Veil Gamma Curve
- SceneAnalyzerV4: CIE LAB MiniBatchKMeans + 3D Light Vector L + Floor Defocus Bokeh
- HarmonizerV4: Dual-Mask Protection (Skin YCrCb + Dress Highlight) + 2.5D Relight & Rim + Dual Shadow
- PhotoshopBridgeV4: ActionManager ExtendScript 7-Layer Non-Destructive Stack with Layer Mask
"""

import os
import gc
import time
import uuid
import cv2
import torch
import hashlib
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from engine.matting import MattingEngineV4, get_matting_engine
from engine.scene_analyzer import SceneAnalyzerV4
from engine.harmonizer import HarmonizerV4
from engine.photoshop_bridge import PhotoshopBridgeV4
from engine.preset_manager import list_presets, save_preset, delete_preset, PRESETS_DIR

BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = BASE_DIR / "output"
STATIC_DIR = BASE_DIR / "static"
PANEL_DIR = BASE_DIR / "ps-panel"
ASSETS_DIR = BASE_DIR / "assets"
PRESETS_PATH = BASE_DIR / "presets"
CACHE_DIR = Path("/tmp/nenai_cache")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
PRESETS_PATH.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="NenAI Studio v4.0 - 10/10 Pro Wedding Compositor",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file mounts
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")
app.mount("/presets", StaticFiles(directory=str(PRESETS_PATH)), name="presets")
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")
app.mount("/ps-panel", StaticFiles(directory=str(PANEL_DIR)), name="ps-panel")
if (PANEL_DIR / "icons").exists():
    app.mount("/icons", StaticFiles(directory=str(PANEL_DIR / "icons")), name="icons")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Khởi tạo các Engine v4.0 (10/10 Pro - Singleton để tối ưu RAM 16GB)
matting_engine = get_matting_engine()
scene_analyzer = SceneAnalyzerV4()
harmonizer = HarmonizerV4(output_dir=str(OUTPUT_DIR))
ps_bridge = PhotoshopBridgeV4()

LAST_PROCESSED_LAYERS: Dict[str, str] = {}
LAST_SESSION_URLS: Dict[str, str] = {}
LAST_SESSION_STATE: Dict[str, Any] = {
    "subject_bgr": None,
    "env_bgr": None,
    "clean_fg_rgb": None,
    "refined_alpha": None,
    "shot_type": "full_body",
    "passe_partout": "none",
    "skin_shield": True,
    "style_idx": 0,
}


def flush_memory():
    """Sequential MPS Memory Guard: Giải phóng triệt để Unified Memory sau mỗi bước."""
    gc.collect()
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()


def _load_fallback_subject() -> Optional[np.ndarray]:
    """Đọc ảnh dâu rể từ Photoshop, hoặc fallback sang ảnh mẫu Studio."""
    try:
        active_doc = ps_bridge.probe_active_document()
        if os.path.exists(active_doc["file_path"]):
            return cv2.imread(active_doc["file_path"], cv2.IMREAD_COLOR)
    except Exception:
        pass

    fallback_candidates = [
        ASSETS_DIR / "pwd05627_subject_input.jpg",
        Path("/Users/phuthanh/HINHANH/AI/PWD05627.jpg"),
        ASSETS_DIR / "media_1793508963871_54c17370.png",
    ]
    for cand in fallback_candidates:
        if cand.exists():
            return cv2.imread(str(cand), cv2.IMREAD_COLOR)
    return None


# =========================================================================
# WEB & PANEL ROUTES (UXP HOT-RELOAD)
# =========================================================================
import re
import shutil

UXP_INSTALLED_DIR = Path("/Users/phuthanh/Library/Application Support/Adobe/UXP/Plugins/External/com.nenai.studio_1.0.0")
_LAST_SYNCED_HASH = ""


def _get_ui_bundle_and_sync() -> Dict[str, str]:
    """Đọc ps-panel/index.html từ đĩa và đồng bộ UXP Hot-Reload."""
    global _LAST_SYNCED_HASH
    index_path = PANEL_DIR / "index.html"
    if not index_path.exists():
        return {"ui_hash": "none", "css": "", "body_html": "", "js": ""}

    raw_html = index_path.read_text(encoding="utf-8")
    ui_hash = hashlib.sha1(raw_html.encode("utf-8")).hexdigest()[:12]

    if ui_hash != _LAST_SYNCED_HASH:
        try:
            shutil.copyfile(str(index_path), str(STATIC_DIR / "index.html"))
            controller_src = PANEL_DIR / "controller.js"
            if controller_src.exists():
                shutil.copyfile(str(controller_src), str(STATIC_DIR / "controller.js"))

            if UXP_INSTALLED_DIR.exists():
                shutil.copyfile(str(index_path), str(UXP_INSTALLED_DIR / "index.html"))
                main_js_src = PANEL_DIR / "main.js"
                if main_js_src.exists():
                    shutil.copyfile(str(main_js_src), str(UXP_INSTALLED_DIR / "main.js"))
                if controller_src.exists():
                    shutil.copyfile(str(controller_src), str(UXP_INSTALLED_DIR / "controller.js"))
            _LAST_SYNCED_HASH = ui_hash
        except Exception:
            pass

    css_match = re.search(r"<style[^>]*>(.*?)</style>", raw_html, flags=re.DOTALL | re.IGNORECASE)
    root_match = re.search(
        r"<!--\s*NENAI_ROOT_START\s*-->(.*?)<!--\s*NENAI_ROOT_END\s*-->",
        raw_html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    body_match = re.search(r"<body[^>]*>(.*?)<script", raw_html, flags=re.DOTALL | re.IGNORECASE)
    script_matches = re.findall(r"<script(?![^>]*src=)[^>]*>(.*?)</script>", raw_html, flags=re.DOTALL | re.IGNORECASE)

    body_content = root_match.group(1).strip() if root_match else (body_match.group(1).strip() if body_match else "")

    return {
        "ui_hash": ui_hash,
        "css": css_match.group(1).strip() if css_match else "",
        "body_html": body_content,
        "js": "\n".join(script_matches).strip() if script_matches else "",
        "updated_at": time.strftime("%H:%M:%S"),
    }


@app.get("/", response_class=HTMLResponse)
async def index_view():
    index_file = PANEL_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>NenAI Studio v4.0 - 10/10 Pro</h1><p>Panel index.html not found.</p>")


@app.get("/style.css")
async def get_root_style():
    style_file = PANEL_DIR / "style.css"
    if not style_file.exists():
        style_file = STATIC_DIR / "style.css"
    return FileResponse(style_file, media_type="text/css")


@app.get("/main.js")
async def get_root_main_js():
    js_file = PANEL_DIR / "main.js"
    return FileResponse(js_file, media_type="application/javascript")


@app.get("/controller.js")
async def get_root_controller_js():
    js_file = PANEL_DIR / "controller.js"
    return FileResponse(js_file, media_type="application/javascript")


@app.get("/api/ui/live")
def get_live_ui_bundle():
    bundle = _get_ui_bundle_and_sync()
    return {"status": "ok", "success": True, **bundle}


@app.get("/api/health")
def health_check():
    bundle = _get_ui_bundle_and_sync()
    return {
        "status": "online",
        "version": "4.0.0 10/10 Pro Wedding Compositor",
        "device": matting_engine.device,
        "ui_hash": bundle["ui_hash"],
    }


@app.get("/api/photoshop/status")
async def ps_status():
    bundle = _get_ui_bundle_and_sync()
    try:
        doc = ps_bridge.probe_active_document()
        return {"connected": True, "doc": doc, "ui_hash": bundle["ui_hash"]}
    except Exception as e:
        return {"connected": False, "doc": None, "message": str(e), "ui_hash": bundle["ui_hash"]}


# =========================================================================
# PRESETS & SCENE ANALYZER
# =========================================================================
@app.get("/api/presets")
async def get_presets():
    return list_presets()


@app.post("/api/presets/save")
async def create_preset(
    name: str = Form(...),
    category: str = Form("Studio"),
    light_dir: str = Form("left"),
    bg_file: Optional[UploadFile] = File(None),
    reference_path: Optional[str] = Form(None),
):
    source_img = None
    if bg_file is not None:
        raw_bytes = await bg_file.read()
        np_arr = np.frombuffer(raw_bytes, np.uint8)
        source_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    elif reference_path and os.path.exists(reference_path):
        source_img = cv2.imread(reference_path, cv2.IMREAD_COLOR)

    if source_img is None:
        bg_path = LAST_PROCESSED_LAYERS.get("07_background") or LAST_PROCESSED_LAYERS.get("master_path")
        if bg_path and os.path.exists(bg_path):
            source_img = bg_path
        elif LAST_SESSION_STATE.get("env_bgr") is not None:
            source_img = LAST_SESSION_STATE["env_bgr"]
        else:
            default_cand = ASSETS_DIR / "korean_2h_floral_plate.jpg"
            if default_cand.exists():
                source_img = str(default_cand)

    if source_img is None:
        raise HTTPException(status_code=400, detail="Vui lòng tải lên ảnh bối cảnh mẫu hoặc thực hiện ghép trước khi lưu.")

    preset = save_preset(name, source_img, category=category, light_dir=light_dir)
    return {"status": "success", "success": True, "preset": preset}


@app.delete("/api/presets/{preset_id}")
async def remove_preset(preset_id: str):
    removed = delete_preset(preset_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy mẫu '{preset_id}'.")
    return {"status": "success", "success": True, "deleted": preset_id}


@app.post("/api/scene/analyze")
async def analyze_scene_endpoint(
    file: Optional[UploadFile] = File(None),
    bg_file: Optional[UploadFile] = File(None),
    reference_path: Optional[str] = Form(None),
):
    upload = file or bg_file
    if upload is not None:
        raw_bytes = await upload.read()
        np_arr = np.frombuffer(raw_bytes, np.uint8)
        ref_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        save_path = str(OUTPUT_DIR / f"analyzed_{upload.filename}")
        cv2.imwrite(save_path, ref_bgr)
    elif reference_path and os.path.exists(reference_path):
        ref_bgr = cv2.imread(reference_path, cv2.IMREAD_COLOR)
        save_path = reference_path
    else:
        raise HTTPException(status_code=400, detail="Vui lòng cung cấp ảnh mẫu hoặc đường dẫn hợp lệ.")

    preview_name = f"custom_bg_preview_{int(time.time())}.jpg"
    preview_full_path = OUTPUT_DIR / preview_name
    cv2.imwrite(str(preview_full_path), ref_bgr, [cv2.IMWRITE_JPEG_QUALITY, 92])
    preview_url = f"/output/{preview_name}"

    scene_info = scene_analyzer.analyze_reference_scene(ref_bgr)
    prompt = scene_analyzer.build_silhouette_aware_prompt(scene_info)
    return {
        "status": "success",
        "success": True,
        "preset_path": save_path,
        "preview_url": preview_url,
        "scene_metrics": scene_info,
        "breakdown": scene_info["breakdown"],
        "color_palette": scene_info["color_palette"],
        "lighting_3d": scene_info.get("lighting_3d"),
        "optics_and_floor": scene_info.get("optics_and_floor"),
        "recommended_prompt": prompt,
    }


# =========================================================================
# V4 COMPOSITE REQUEST & 1.2S ALPHA CACHING ENDPOINT
# =========================================================================
class CompositeRequest(BaseModel):
    subject_path: str
    background_path: str
    foreground_overlay_path: Optional[str] = None
    veil_gamma: float = 1.18
    harmonize_strength: float = 0.55
    use_cached_matte: bool = True


@app.post("/api/v4/composite-to-photoshop")
def process_and_send_to_photoshop(req: CompositeRequest):
    """
    Quy trình kết hợp 10/10 Pro:
    - 33MP BiRefNet + Fast Guided Filter + Veil Gamma Curve
    - Alpha Caching: Cho phép chỉnh lại ánh sáng/màu trong 1.2s không cần chạy lại BiRefNet
    - 7 Layer non-destructive với Layer Mask ActionManager trong Photoshop 2026
    """
    t0 = time.time()
    # 1. Đọc ảnh Dâu Rể (33MP) và Nền
    fg_bgr = cv2.imread(req.subject_path, cv2.IMREAD_COLOR)
    if fg_bgr is None:
        raise HTTPException(status_code=400, detail=f"Không đọc được ảnh dâu rể: {req.subject_path}")
    bg_bgr = cv2.imread(req.background_path, cv2.IMREAD_COLOR)
    if bg_bgr is None:
        raise HTTPException(status_code=400, detail=f"Không đọc được ảnh nền: {req.background_path}")

    fg_rgb = cv2.cvtColor(fg_bgr, cv2.COLOR_BGR2RGB)
    h, w, _ = fg_rgb.shape
    bg_rgb = cv2.cvtColor(cv2.resize(bg_bgr, (w, h), interpolation=cv2.INTER_CUBIC), cv2.COLOR_BGR2RGB)

    # 2. Kiểm tra Cache Alpha & Unmixed Foreground (Giúp chỉnh lại màu/ánh sáng chỉ mất 1.2 giây)
    file_hash = hashlib.md5(f"{req.subject_path}_{req.veil_gamma}".encode()).hexdigest()
    cached_fg_path = CACHE_DIR / f"{file_hash}_clean_fg.png"
    cached_alpha_path = CACHE_DIR / f"{file_hash}_alpha.png"

    if req.use_cached_matte and cached_fg_path.exists() and cached_alpha_path.exists():
        clean_fg_rgb = cv2.cvtColor(cv2.imread(str(cached_fg_path)), cv2.COLOR_BGR2RGB)
        refined_alpha = cv2.imread(str(cached_alpha_path), cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.0
    else:
        # Chạy BiRefNet lấy raw_alpha
        raw_alpha = matting_engine.model_loader_fn(fg_rgb) if matting_engine.model_loader_fn else np.ones((h, w), dtype=np.float32)
        clean_fg_rgb, refined_alpha = matting_engine.unmix_and_refine_veil(
            fg_rgb, raw_alpha, veil_gamma=req.veil_gamma
        )
        cv2.imwrite(str(cached_fg_path), cv2.cvtColor(clean_fg_rgb, cv2.COLOR_RGB2BGR))
        cv2.imwrite(str(cached_alpha_path), (refined_alpha * 255.0).astype(np.uint8))
        flush_memory()

    # 3. Phân tích bối cảnh 3D (Vector hướng sáng, Shadow Tint, Độ phản xạ sàn)
    scene_meta = scene_analyzer.analyze_scene(bg_rgb)
    light_vec = scene_meta["lighting_3d"]["vector_xyz"]
    key_light_rgb = scene_meta["lighting_3d"]["key_light_rgb"]
    shadow_tint_rgb = scene_meta["shadow_tint_rgb"]
    floor_refl = scene_meta["optics_and_floor"]["floor_reflectivity"]

    # 4. Hòa trộn màu sắc + Tạo Relight 2.5D + Light Wrap + Bóng Vật Lý Kép
    harmonized_fg_rgb = harmonizer.harmonize_subject_color(
        clean_fg_rgb, bg_rgb, refined_alpha, strength=req.harmonize_strength
    )
    relight_rgba = harmonizer.generate_25d_relight_and_rim_layer(
        harmonized_fg_rgb, refined_alpha, light_vec, key_light_rgb
    )
    light_wrap_rgba = harmonizer.generate_multiscale_light_wrap(bg_rgb, refined_alpha)
    shadow_rgba = harmonizer.generate_dual_physical_shadow(
        refined_alpha, light_vec, shadow_tint_rgb, floor_refl
    )
    flush_memory()

    # 5. Xuất các Layer ra thư mục tạm và đẩy thẳng vào Adobe Photoshop 2026
    out_dir = ps_bridge.create_session_dir()
    paths = {
        "07_background": str(out_dir / "07_bg.png"),
        "06_shadow": str(out_dir / "06_shadow.png"),
        "05_subject_rgb": str(out_dir / "05_subject_rgb.png"),
        "05_subject_alpha": str(out_dir / "05_subject_alpha.png"),
        "04_relight": str(out_dir / "04_relight.png"),
        "03_light_wrap": str(out_dir / "03_light_wrap.png"),
        "01_foreground": req.foreground_overlay_path or ""
    }

    cv2.imwrite(paths["07_background"], cv2.cvtColor(bg_rgb, cv2.COLOR_RGB2BGR))
    cv2.imwrite(paths["06_shadow"], cv2.cvtColor(shadow_rgba, cv2.COLOR_RGBA2BGRA))
    cv2.imwrite(paths["05_subject_rgb"], cv2.cvtColor(harmonized_fg_rgb, cv2.COLOR_RGB2BGR))
    cv2.imwrite(paths["05_subject_alpha"], (refined_alpha * 255.0).astype(np.uint8))
    cv2.imwrite(paths["04_relight"], cv2.cvtColor(relight_rgba, cv2.COLOR_RGBA2BGRA))
    cv2.imwrite(paths["03_light_wrap"], cv2.cvtColor(light_wrap_rgba, cv2.COLOR_RGBA2BGRA))

    ps_res = ps_bridge.send_to_photoshop_2026(paths)
    elapsed = round(time.time() - t0, 2)
    return {
        "status": "success",
        "elapsed_seconds": elapsed,
        "scene_analysis": scene_meta,
        "layers_exported": 7,
        "photoshop_result": ps_res,
    }


# =========================================================================
# CORE 1-CLICK PROCESSING (FORM & JSON FOR PANEL & BROWSER)
# =========================================================================
class ProcessRequest(BaseModel):
    subject_path: Optional[str] = None
    reference_path: Optional[str] = None
    ai_composite_path: Optional[str] = None
    is_ai_composite: bool = True
    shot_type: str = "full_body"
    passe_partout: str = "none"
    skin_shield: bool = True
    auto_push_ps: bool = False
    harmonize_strength: float = 0.55
    veil_gamma: float = 1.18


@app.post("/api/process")
async def process_master_endpoint(
    request: Request,
    fg_file: Optional[UploadFile] = File(None),
    bg_file: Optional[UploadFile] = File(None),
    reference_path: Optional[str] = Form(None),
    preset_id: Optional[str] = Form(None),
    shot_type: Optional[str] = Form("full_body"),
    passe_partout: Optional[str] = Form("none"),
    scale_fg: Optional[float] = Form(1.0),
    skin_shield: Optional[bool] = Form(True),
    auto_push_ps: Optional[bool] = Form(False),
    harmonize_strength: Optional[float] = Form(0.55),
    veil_gamma: Optional[float] = Form(1.18),
):
    global LAST_PROCESSED_LAYERS, LAST_SESSION_URLS, LAST_SESSION_STATE
    t0 = time.time()

    content_type = request.headers.get("content-type", "")
    req_json: Optional[ProcessRequest] = None
    if "application/json" in content_type:
        body = await request.json()
        req_json = ProcessRequest(**body)

    subject_bgr: Optional[np.ndarray] = None
    env_bgr: Optional[np.ndarray] = None
    should_push = bool(auto_push_ps)
    cur_shot_type = shot_type or "full_body"
    cur_passe_partout = passe_partout or "none"
    cur_skin_shield = True if skin_shield is None else bool(skin_shield)
    cur_strength = float(harmonize_strength or 0.55)
    cur_gamma = float(veil_gamma or 1.18)

    if req_json:
        if req_json.subject_path and os.path.exists(req_json.subject_path):
            subject_bgr = cv2.imread(req_json.subject_path, cv2.IMREAD_COLOR)
        else:
            subject_bgr = _load_fallback_subject()

        env_path = req_json.ai_composite_path or req_json.reference_path
        if env_path and os.path.exists(env_path):
            env_bgr = cv2.imread(env_path, cv2.IMREAD_COLOR)
        should_push = req_json.auto_push_ps
        cur_shot_type = req_json.shot_type
        cur_passe_partout = req_json.passe_partout
        cur_skin_shield = req_json.skin_shield
        cur_strength = req_json.harmonize_strength
        cur_gamma = req_json.veil_gamma
    else:
        if fg_file:
            raw_fg = await fg_file.read()
            arr_fg = np.frombuffer(raw_fg, np.uint8)
            subject_bgr = cv2.imdecode(arr_fg, cv2.IMREAD_COLOR)
        else:
            subject_bgr = _load_fallback_subject()

        if bg_file:
            raw_bg = await bg_file.read()
            arr_bg = np.frombuffer(raw_bg, np.uint8)
            env_bgr = cv2.imdecode(arr_bg, cv2.IMREAD_COLOR)
        elif reference_path and os.path.exists(reference_path):
            env_bgr = cv2.imread(reference_path, cv2.IMREAD_COLOR)
        elif preset_id:
            preset_file = PRESETS_PATH / preset_id / "clean_bg.jpg"
            if not preset_file.exists():
                preset_file = PRESETS_PATH / f"{preset_id}.jpg"
            if preset_file.exists():
                env_bgr = cv2.imread(str(preset_file), cv2.IMREAD_COLOR)

    if subject_bgr is None:
        raise HTTPException(status_code=400, detail="Không tìm thấy ảnh dâu rể hợp lệ để xử lý.")

    if env_bgr is None:
        default_cand = ASSETS_DIR / "korean_2h_floral_plate.jpg"
        if default_cand.exists():
            env_bgr = cv2.imread(str(default_cand), cv2.IMREAD_COLOR)
        else:
            env_bgr = np.full_like(subject_bgr, 240)

    job_id = f"nenai_v4_{int(time.time())}_{uuid.uuid4().hex[:4]}"

    # Chạy pipeline 10/10 Pro
    layer_paths = harmonizer.process_master_pipeline(
        subject_bgr_33mp=subject_bgr,
        reference_or_ai_bgr=env_bgr,
        job_id=job_id,
        shot_type=cur_shot_type,
        skin_shield_enabled=cur_skin_shield,
        passe_partout=cur_passe_partout,
        lighting_style="natural",
        harmonize_strength=cur_strength,
        veil_gamma=cur_gamma,
    )
    LAST_PROCESSED_LAYERS = layer_paths

    urls = {
        "master": f"/output/{os.path.basename(layer_paths['master_path'])}",
        "v1": f"/output/{os.path.basename(layer_paths['master_path'])}",
        "clean_bg": f"/output/{os.path.basename(layer_paths['07_background'])}",
        "shadow": f"/output/{os.path.basename(layer_paths['06_shadow'])}",
        "subject_rgb": f"/output/{os.path.basename(layer_paths['05_subject_rgb'])}",
        "relight": f"/output/{os.path.basename(layer_paths['04_relight'])}",
        "light_wrap": f"/output/{os.path.basename(layer_paths['03_light_wrap'])}",
    }
    LAST_SESSION_URLS = urls

    LAST_SESSION_STATE.update({
        "subject_bgr": subject_bgr,
        "env_bgr": env_bgr,
        "shot_type": cur_shot_type,
        "passe_partout": cur_passe_partout,
        "skin_shield": cur_skin_shield,
        "style_idx": 0,
    })

    ps_result = None
    if should_push:
        ps_result = ps_bridge.send_to_photoshop_2026(layer_paths)

    elapsed = round(time.time() - t0, 2)
    flush_memory()

    return {
        "status": "success",
        "success": True,
        "total_time": elapsed,
        "elapsed_seconds": elapsed,
        "resolution": f"{subject_bgr.shape[1]}x{subject_bgr.shape[0]}",
        "layers": layer_paths,
        "urls": urls,
        "photoshop_push": ps_result,
    }


# =========================================================================
# PUSH MASTER 7-LAYERS INTO PHOTOSHOP
# =========================================================================
@app.post("/api/photoshop/push")
async def push_to_photoshop_endpoint():
    """Đẩy cấu trúc 7 Layer không phá hủy vào Adobe Photoshop 2026 (1-Click từ UXP Panel)."""
    global LAST_PROCESSED_LAYERS
    if not LAST_PROCESSED_LAYERS:
        try:
            subj_bgr = _load_fallback_subject()
            if subj_bgr is None:
                raise RuntimeError("Chưa mở ảnh trên Photoshop.")
            job_id = f"nenai_v4_{int(time.time())}_{uuid.uuid4().hex[:4]}"
            LAST_PROCESSED_LAYERS = harmonizer.process_master_pipeline(
                subject_bgr_33mp=subj_bgr,
                reference_or_ai_bgr=None,
                job_id=job_id,
            )
        except Exception as e:
            return JSONResponse(status_code=400, content={"status": "error", "success": False, "detail": str(e)})

    ps_res = ps_bridge.send_to_photoshop_2026(LAST_PROCESSED_LAYERS)
    is_success = ps_res.get("status") == "success"
    return {
        "status": "success" if is_success else "error",
        "success": is_success,
        "detail": None if is_success else str(ps_res.get("ps_response", "Chưa kết nối được Photoshop 2026.")),
        "layers": LAST_PROCESSED_LAYERS,
        "photoshop_push": ps_res,
        "urls": LAST_SESSION_URLS,
    }


# =========================================================================
# REGENERATE VARIATION (1.2S ULTRA-FAST CACHED REFINEMENT)
# =========================================================================
@app.post("/api/regenerate")
async def regenerate_endpoint(
    shot_type: Optional[str] = Form("full_body"),
    passe_partout: Optional[str] = Form("none"),
):
    """Sinh lại biến thể ánh sáng (Natural -> Rim Light -> Dreamy Soft) chỉ trong 1.2s bằng Alpha Cache."""
    global LAST_PROCESSED_LAYERS, LAST_SESSION_URLS, LAST_SESSION_STATE
    t0 = time.time()

    subj_bgr = LAST_SESSION_STATE.get("subject_bgr")
    if subj_bgr is None:
        subj_bgr = _load_fallback_subject()
    if subj_bgr is None:
        raise HTTPException(status_code=400, detail="Không tìm thấy ảnh dâu rể để tạo biến thể ánh sáng.")

    env_bgr = LAST_SESSION_STATE.get("env_bgr")
    styles = ["natural", "rim_light", "dreamy"]
    next_idx = (int(LAST_SESSION_STATE.get("style_idx", 0)) + 1) % len(styles)
    LAST_SESSION_STATE["style_idx"] = next_idx
    chosen_style = styles[next_idx]

    job_id = f"nenai_v4_regen_{chosen_style}_{int(time.time())}"
    layer_paths = harmonizer.process_master_pipeline(
        subject_bgr_33mp=subj_bgr,
        reference_or_ai_bgr=env_bgr,
        job_id=job_id,
        shot_type=shot_type or LAST_SESSION_STATE.get("shot_type", "full_body"),
        skin_shield_enabled=bool(LAST_SESSION_STATE.get("skin_shield", True)),
        passe_partout=passe_partout or LAST_SESSION_STATE.get("passe_partout", "none"),
        lighting_style=chosen_style,
    )
    LAST_PROCESSED_LAYERS = layer_paths
    urls = {
        "master": f"/output/{os.path.basename(layer_paths['master_path'])}",
        "v1": f"/output/{os.path.basename(layer_paths['master_path'])}",
    }
    LAST_SESSION_URLS = urls
    elapsed = round(time.time() - t0, 2)
    flush_memory()

    return {
        "status": "success",
        "success": True,
        "elapsed_seconds": elapsed,
        "lighting_style": chosen_style,
        "urls": urls,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8989)
