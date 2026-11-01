# Đặc Tả Kiến Trúc Hệ Thống & Giao Thức Kết Nối - NenAI Studio v8.1 PRO
> **Tài liệu kỹ thuật hệ thống (System Architecture, API Specification & Photoshop Integration)**

---

## 1. Cấu Trúc Tổng Thể Dự Án

```text
/Users/phuthanh/APP_CaNhan/NenAI/
├── README.md                 # Tài liệu tổng quan dự án & Bảng đánh giá năng lực AI
├── AI_PIPELINE.md            # Đặc tả chuyên sâu thuật toán xử lý hình ảnh 33MP
├── WORKFLOW_STUDIO.md        # Cẩm nang quy trình chụp ảnh & mẹo hậu kỳ Retoucher
├── SPEC_SYSTEM.md            # Tài liệu đặc tả hệ thống, API & JSX Bridge (File này)
├── run_app.sh                # Script khởi chạy Gateway FastAPI (Port 8989)
├── NenAI_Studio.command      # File thực thi trực tiếp từ Finder
├── app.py                    # Gateway FastAPI chính & Quản lý phiên làm việc
├── engine/                   # Các module xử lý AI cốt lõi
│   ├── __init__.py
│   ├── matting.py            # MattingEngineV3: BiRefNet MPS, Chroma Guided Filter, Dual-Plane Geometry
│   ├── background_cleaner.py # Tự động phát hiện & xóa nhân vật mẫu, xóa UI mạng xã hội
│   ├── scene_analyzer.py     # SceneAnalyzerV3: Đo đường chân trời y_horizon, trích xuất bảng màu & SIFT/RANSAC
│   ├── harmonizer.py         # HarmonizerMasterV3: Bóng sàn 3 tầng, Light-Wrap & bộ xuất 5 Layer 33MP
│   ├── photoshop_bridge.py   # PhotoshopBridgeV3: Điều khiển AppleScript JSX trong Photoshop 2026
│   └── preset_manager.py     # Quản lý kho mẫu bối cảnh Studio (Preset Vault)
├── ps-panel/                 # Photoshop UXP Plugin (Giao diện neo trong Photoshop 2026)
│   ├── manifest.json         # Cấu hình định danh UXP Manifest v6 & cấp quyền mạng/ổ đĩa
│   ├── index.html            # Giao diện Flexbox tiếng Việt tối ưu UXP (Hot-Reload)
│   ├── style.css             # Giao diện Dark Gold & Titanium chuẩn Adobe UI
│   ├── controller.js         # Logic điều phối giao diện, Event Delegation & gọi API
│   ├── main.js               # Logic khởi động UXP & Engine Live Hot-Reload
│   └── icons/                # Icons & thumbnails xem trước mẫu
├── presets/                  # Kho lưu trữ mẫu bối cảnh ghép sẵn (Studio Vault)
│   ├── korean_baby_flowers_01/
│   ├── palace_gold_02/
│   ├── fineart_mottled_03/
│   └── sanh_cung_dien_chau_au_04/
├── assets/                   # Tài nguyên ảnh mẫu studio kiểm thử (33MP)
└── output/                   # Thư mục lưu kết quả kết xuất tạm thời (33MP layers & previews)
```

---

## 2. Đặc Tả API Backend (FastAPI Service)

Server cục bộ chạy tại: `http://127.0.0.1:8989`  
CORS kích hoạt cho tất cả nguồn (`allow_origins=["*"]`) để UXP Panel và Web Preview kết nối ổn định.

### 2.1. Kiểm tra trạng thái hệ thống (Health Check)
- **Endpoint:** `GET /api/health`
- **Mô tả:** Trả về trạng thái hoạt động của gateway, thiết bị gia tốc (MPS Metal) và mã hash giao diện hiện tại.
- **Phản hồi mẫu:**
  ```json
  {
    "status": "online",
    "version": "8.1.0 Ultra-Studio Master Edition",
    "device": "mps",
    "ui_hash": "a1b2c3d4e5f6"
  }
  ```

### 2.2. Kiểm tra trạng thái Photoshop 2026
- **Endpoint:** `GET /api/photoshop/status`
- **Mô tả:** Thăm dò xem Adobe Photoshop 2026 có đang mở không và đọc thông số document đang active (đường dẫn, kích thước, tên file).
- **Phản hồi mẫu:**
  ```json
  {
    "connected": true,
    "doc": {
      "file_path": "/Users/phuthanh/HINHANH/AI/PWD05627.jpg",
      "path": "/Users/phuthanh/HINHANH/AI/PWD05627.jpg",
      "width": 4672,
      "height": 7008,
      "doc_name": "PWD05627.jpg",
      "name": "PWD05627.jpg"
    },
    "ui_hash": "a1b2c3d4e5f6"
  }
  ```

### 2.3. Đọc Gói Giao Diện Trực Tiếp (Live UI Hot-Reload)
- **Endpoint:** `GET /api/ui/live`
- **Mô tả:** Trả về toàn bộ nội dung HTML, CSS và JavaScript của Panel từ `ps-panel/index.html` kèm mã băm SHA1. Giúp UXP Panel tự động cập nhật giao diện ngay lập tức khi nhà phát triển sửa code mà không cần tắt/mở Photoshop.
- **Phản hồi mẫu:**
  ```json
  {
    "status": "ok",
    "success": true,
    "ui_hash": "3f9a12c8b091",
    "css": "/* ... */",
    "body_html": "<div id='nenaiAppRoot'>...</div>",
    "js": "/* ... */",
    "updated_at": "22:45:10"
  }
  ```

### 2.4. Phân tích bối cảnh & Trích xuất bảng màu (Scene Analyzer)
- **Endpoint:** `POST /api/scene/analyze`
- **Đầu vào (FormData):**
  - `file` hoặc `bg_file`: File ảnh nền mẫu (UploadFile, tùy chọn).
  - `reference_path`: Đường dẫn file nền mẫu trên ổ cứng (string, tùy chọn).
- **Mô tả:** Đo đường giao tuyến chân tường `y_horizon`, trích xuất 3 mã màu HEX (Màu Sàn, Màu Tường, Điểm Trắng Hoa), phân tích cấu trúc 3 tầng (Tiền cảnh, Trung cảnh, Hậu cảnh) và sinh gợi ý prompt bối cảnh ôm sát tà váy.
- **Phản hồi mẫu:**
  ```json
  {
    "status": "success",
    "success": true,
    "preset_path": "/Users/phuthanh/APP_CaNhan/NenAI/output/analyzed_sample.jpg",
    "scene_metrics": {
      "y_bg_horizon": 0.773,
      "light_direction": "right_to_left",
      "gobo_angle_deg": -32.0,
      "floor_roughness_std": 48.79
    },
    "color_palette": {
      "floor_hex": "#E6D8C2",
      "wall_hex": "#DFD7C4",
      "flower_hex": "#CDBF9B"
    },
    "breakdown": {
      "tien_canh": { "tieu_de": "Nền Dưới Chân (Floor Plane)", "mat_san": "..." },
      "trung_canh": { "tieu_de": "Trung Cảnh (Midground)", "vom_hoa": "..." },
      "hau_canh_va_nen": { "tieu_de": "Nền Phía Sau (Backdrop Wall)", "tuong_nen": "..." }
    },
    "recommended_prompt": "Korean minimal studio, floor contact shadow, 85mm f/1.8"
  }
  ```

### 2.5. Xử lý toàn trình 1-Click (Master Pipeline)
- **Endpoint:** `POST /api/process`
- **Hỗ trợ 2 định dạng:** JSON (`application/json`) hoặc Multipart (`multipart/form-data`).
- **Các tham số đầu vào:**
  - `fg_file` / `subject_path`: Ảnh dâu rể (nếu không truyền, tự động đọc ảnh active từ Photoshop 2026).
  - `bg_file` / `reference_path` / `ai_composite_path`: Ảnh bối cảnh mẫu hoặc bản ghép AI cần tinh chỉnh.
  - `preset_id`: ID của mẫu trong Kho Mẫu (ví dụ: `korean_baby_flowers_01`).
  - `shot_type`: `"full_body"` (mặc định), `"half_body"`, hoặc `"portrait"`.
  - `passe_partout`: `"none"` (không bo), `"white"` (viền trắng), hoặc `"cream"` (viền ngà).
  - `skin_shield`: `true` (mặc định bảo vệ da dâu rể) hoặc `false`.
  - `auto_push_ps`: `true` (tự động đẩy vào Photoshop sau khi xử lý) hoặc `false`.
- **Phản hồi mẫu:**
  ```json
  {
    "status": "success",
    "success": true,
    "total_time": 5.49,
    "elapsed_seconds": 5.49,
    "resolution": "4672x7008",
    "layers": {
      "master_path": "/Users/phuthanh/APP_CaNhan/NenAI/output/nenai_v4_..._00_master_studio.jpg",
      "layer1_floral_fg": "/Users/phuthanh/APP_CaNhan/NenAI/output/nenai_v4_..._01_floral_foreground.png",
      "layer2_subject_33mp": "/Users/phuthanh/APP_CaNhan/NenAI/output/nenai_v4_..._02_subject_33mp.png",
      "layer3_light_wrap": "/Users/phuthanh/APP_CaNhan/NenAI/output/nenai_v4_..._03_light_wrap.png",
      "layer4_real_shadow": "/Users/phuthanh/APP_CaNhan/NenAI/output/nenai_v4_..._04_real_floor_shadow.jpg",
      "layer5_clean_bg": "/Users/phuthanh/APP_CaNhan/NenAI/output/nenai_v4_..._05_clean_backdrop_33mp.jpg"
    },
    "urls": {
      "master": "/output/nenai_v4_..._00_master_studio.jpg",
      "floral_fg": "/output/nenai_v4_..._01_floral_foreground.png",
      "subject_33mp": "/output/nenai_v4_..._02_subject_33mp.png",
      "light_wrap": "/output/nenai_v4_..._03_light_wrap.png",
      "real_shadow": "/output/nenai_v4_..._04_real_floor_shadow.jpg",
      "clean_bg": "/output/nenai_v4_..._05_clean_backdrop_33mp.jpg"
    },
    "photoshop_push": { "status": "success", "ps_response": "SUCCESS_5_LAYERS" }
  }
  ```

### 2.6. Đẩy 5 Layer vào Photoshop (Push to Photoshop)
- **Endpoint:** `POST /api/photoshop/push`
- **Mô tả:** Gọi AppleScript thực thi script JSX bên trong Photoshop 2026 để xếp 5 Layer chuyên nghiệp vào tài liệu đang active.
- **Phản hồi mẫu:**
  ```json
  {
    "status": "success",
    "success": true,
    "photoshop_push": {
      "status": "success",
      "ps_response": "SUCCESS_5_LAYERS"
    }
  }
  ```

### 2.7. Tinh chỉnh ánh sáng (Regenerate Variations)
- **Endpoint:** `POST /api/regenerate`
- **Mô tả:** Tái tạo ánh sáng theo chu kỳ 3 phong cách: `natural` $\rightarrow$ `rim_light` $\rightarrow$ `dreamy` trong ~2 giây mà không cần tính toán lại bước bóc tách BiRefNet.
- **Phản hồi mẫu:**
  ```json
  {
    "status": "success",
    "success": true,
    "lighting_style": "rim_light",
    "urls": {
      "master": "/output/nenai_v8_regen_rim_light_..._00_master_studio.jpg"
    }
  }
  ```

### 2.8. Quản lý Kho Bối Cảnh Studio (Studio Preset Vault)
- **`GET /api/presets`**: Liệt kê toàn bộ các bối cảnh mẫu có trong thư mục `presets/`.
- **`POST /api/presets/save`**: Lưu một bối cảnh mới vào kho mẫu (tự động phân tích bảng màu HEX và tạo ảnh thumbnail).
- **`DELETE /api/presets/{preset_id}`**: Xóa một mẫu khỏi kho.

---

## 3. Giao Thức Điều Khiển Photoshop Bridge (AppleScript & JSX)

Hệ thống sử dụng module `engine/photoshop_bridge.py` để gửi lệnh AppleScript trực tiếp đến Adobe Photoshop 2026:

```javascript
#target photoshop
app.bringToFront();

(function() {
    try {
        if (app.documents.length === 0) return "ERR_NO_DOC";
        var doc = app.activeDocument;
        var origRuler = app.preferences.rulerUnits;
        app.preferences.rulerUnits = Units.PIXELS;

        function placeFileAsLayer(filePath, layerName, blendMode, opacityVal, visibleVal, targetGroup) {
            var f = new File(filePath);
            if (!f.exists) return null;

            var tempDoc = app.open(f);
            var lyr = tempDoc.activeLayer.duplicate(doc, ElementPlacement.PLACEATBEGINNING);
            tempDoc.close(SaveOptions.DONOTSAVECHANGES);
            app.activeDocument = doc;

            lyr.name = layerName;
            if (blendMode) lyr.blendMode = blendMode;
            if (opacityVal !== undefined) lyr.opacity = opacityVal;
            if (visibleVal !== undefined) lyr.visible = visibleVal;
            if (targetGroup) lyr.move(targetGroup, ElementPlacement.PLACEATBEGINNING);
            return lyr;
        }

        try {
            // Xóa group cũ nếu có để tránh trùng lặp layer
            try { var old = doc.layerSets.getByName("[NenAI v3.0 - Studio Wedding 33MP]"); if (old) old.remove(); } catch(e) {}
            
            var group = doc.layerSets.add();
            group.name = "[NenAI v3.0 - Studio Wedding 33MP]";

            // 5. Nền bối cảnh (dưới cùng)
            placeFileAsLayer(p_bg, "[AI Nền] Bối Cảnh Hoa & Nắng Gobo 33MP", BlendMode.NORMAL, 100, true, group);

            // 4. Bóng thật sàn nhà (Multiply)
            placeFileAsLayer(p_shadow, "[Bóng Thật] Bóng Gấu Váy Gốc (Multiply)", BlendMode.MULTIPLY, 100, true, group);

            // 3. Dâu rể nét gốc 33MP + Voan cưới
            placeFileAsLayer(p_subject, "[33MP Gốc] Dâu Rể & Voan Cưới (Pixel-Lock)", BlendMode.NORMAL, 100, true, group);

            // 2. Light Wrap kem ấm
            placeFileAsLayer(p_wrap, "[Ánh Sáng] Light Wrap Kem Ấm", BlendMode.SOFTLIGHT, 38, true, group);

            // 1. Hoa tiền cảnh ôm sát mép váy
            placeFileAsLayer(p_floral, "[Tiền Cảnh] Cành Hoa Ôm Mép Váy", BlendMode.NORMAL, 100, true, group);

            // 0. Bản Master gộp hoàn chỉnh (tắt mắt dự phòng)
            placeFileAsLayer(p_master, "[Bản Gộp Master] Hoàn Thiện 33MP", BlendMode.NORMAL, 100, false, group);

        } finally {
            app.preferences.rulerUnits = origRuler;
        }
        return "SUCCESS_5_LAYERS";
    } catch(err) {
        return "ERR_JSX: " + err.toString();
    }
})();
```

---

## 4. Đặc Tả UXP Manifest v6 (`manifest.json`)

Plugin UXP được cấu hình với chuẩn Manifest v6 hiện đại nhất của Adobe:

```json
{
  "id": "com.nenai.studio",
  "name": "NenAI Studio - Ghép Nền Cưới",
  "version": "1.0.0",
  "main": "index.html",
  "manifestVersion": 6,
  "host": {
    "app": "PS",
    "minVersion": "23.0.0"
  },
  "requiredPermissions": {
    "localFileSystem": "fullAccess",
    "network": {
      "domains": "all"
    },
    "clipboard": "readAndWrite",
    "allowCodeGenerationFromStrings": true
  },
  "entrypoints": [
    {
      "type": "panel",
      "id": "com.nenai.studio.panel",
      "label": {
        "default": "NenAI Studio - Ghép Nền Cưới"
      },
      "preferredDockedSize": { "width": 380, "height": 720 },
      "preferredFloatingSize": { "width": 380, "height": 720 }
    }
  ]
}
```

---

## 5. Cơ Chế Live Hot-Reload Bảng Điều Khiển Trong Photoshop

Nhờ tính năng `Live Hot-Reload` được tích hợp trong `app.py` và `ps-panel/main.js`:
1. Mỗi khi file `ps-panel/index.html` hoặc `controller.js` được lưu trên ổ cứng, gateway tự động tính toán mã hash SHA1 mới và sao chép gói cập nhật sang thư mục UXP Plugin của Adobe.
2. Panel UXP định kỳ kiểm tra hoặc khi người dùng nhấp vào biểu tượng chữ **`N`** (Gold Brand Icon), Panel sẽ nạp trực tiếp CSS và DOM mới vào `#nenaiAppRoot`.
3. Retoucher và lập trình viên có thể thay đổi màu sắc, nút bấm, tính năng giao diện mà **không bao giờ phải tắt hay mở lại Photoshop**.
