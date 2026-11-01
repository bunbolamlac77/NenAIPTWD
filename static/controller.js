/**
 * NenAI Studio v8.1 PRO — Controller & UI Event Dispatcher
 * 100% Adobe UXP & Web Compatible.
 * Tuyệt đối không dùng inline onclick="..." vì Adobe UXP CSP chặn thực thi inline.
 * Sử dụng Event Delegation + addEventListener trực tiếp.
 */

(function () {
  "use strict";

  console.log("[NenAI Controller] Khởi tạo bộ điều khiển giao diện NenAI Studio v8.1 PRO...");

  var API_BASE = (window.location && window.location.origin && window.location.origin.indexOf("http") === 0)
    ? window.location.origin
    : "http://127.0.0.1:8989";

  window.currentShotType = window.currentShotType || "full_body";
  window.currentPresetId = window.currentPresetId || "korean_baby_flowers_01";
  window.currentMat = window.currentMat || "none";
  window.optSkinShield = (window.optSkinShield !== undefined) ? window.optSkinShield : true;
  window.optCatchlight = (window.optCatchlight !== undefined) ? window.optCatchlight : true;
  window.showingOrigCompare = false;
  window.uploadedBgFile = null;
  window.uploadedBgPath = null;
  window.uploadedBgName = null;

  window.PRESET_META = window.PRESET_META || {
    "korean_baby_flowers_01": {
      title: "Hàn Quốc Botanical Sunlight (v8.1)",
      preview: "icons/preview_korean_v8.jpg",
      thumb: "icons/thumb_korean_v8.jpg",
      tag: "v8.1 3D",
      sub: "Nắng xiên & Hoa rum",
      floorHex: "#E2D5C1",
      wallHex: "#EFE5D4",
      flowerHex: "#F7F2E7",
      fg: "Cụm hoa hồng trắng & lá khuynh diệp mờ bokeh f/1.8 ở hai góc dưới, cánh hoa rơi quanh mũi giày và bóng tiếp xúc sàn 3D.",
      mid: "Đăng ký SIFT + RANSAC Kép (<0.5px), giữ 100% nét mặt, tóc và hạt ren 33MP kết hợp bình hoa rum trắng hai bên.",
      bg: "Tường phào chỉ kem ấm & vệt nắng cửa sổ Gobo xiên 45°, đồng bộ điểm trắng sơ mi và váy cưới (LAB b = 138)."
    },
    "palace_gold_02": {
      title: "Vòm Hoa Cẩm Thạch Luxury (v8.1)",
      preview: "icons/preview_luxury_v8.jpg",
      thumb: "icons/thumb_luxury_v8.jpg",
      tag: "LUXURY",
      sub: "Sàn đá & Lan hồ điệp",
      floorHex: "#DECAB0",
      wallHex: "#E5D6BE",
      flowerHex: "#F6EFE2",
      fg: "Sàn đá cẩm thạch kem ấm phản chiếu bóng gương đế giày, cánh hoa trắng rơi tự nhiên và hoa hồng bokeh tiền cảnh.",
      mid: "Vòm hoa lan hồ điệp trắng & hồng cổ điển cao 2.4m ôm quanh Dâu Rể với độ chi tiết 33MP.",
      bg: "Hệ cửa sổ vòm kiểu Pháp đón nắng chiều vàng kem ấm áp (LAB b = 143.9), đồng bộ toàn diện da và trang phục."
    },
    "fineart_mottled_03": {
      title: "Sảnh Nắng Cổ Điển (v8.1)",
      preview: "icons/preview_conservatory_v8.jpg",
      thumb: "icons/thumb_conservatory_v8.jpg",
      tag: "CLASSIC",
      sub: "Cửa vòm nắng ấm",
      floorHex: "#DFCBB2",
      wallHex: "#EAE0CF",
      flowerHex: "#F5EFE6",
      fg: "Mặt sàn gạch kem bóng phản xạ ánh nắng cửa sổ, cụm hoa tiền cảnh hai bên tạo chiều sâu 3 lớp.",
      mid: "Bố cục đối xứng sang trọng tôn dáng vest kem chú rể và độ phồng tà váy cưới cô dâu.",
      bg: "Kiến trúc cổ điển châu Âu với ánh sáng khuếch tán mềm mại và quầng sáng viền 360°."
    }
  };
  var PRESET_META = window.PRESET_META;

  window.currentMasterPreviewSrc = window.currentMasterPreviewSrc || PRESET_META["korean_baby_flowers_01"].preview;

  // =========================================================================
  // 1. TOAST NOTIFICATION HELPER
  // =========================================================================
  window.showToast = function (msg, type) {
    type = type || "success";
    var toast = document.getElementById("toast");
    var icon = document.getElementById("toastIcon");
    var text = document.getElementById("toastMsg");
    if (!toast || !icon || !text) return;

    toast.className = type === "error" ? "toast-banner show error" : "toast-banner show";
    icon.textContent = type === "error" ? "⚠️" : "✨";
    text.textContent = msg;

    if (window.__NENAI_TOAST_TIMER) clearTimeout(window.__NENAI_TOAST_TIMER);
    window.__NENAI_TOAST_TIMER = setTimeout(function () {
      toast.className = "toast-banner";
    }, 3600);
  };

  // =========================================================================
  // 2. SO SÁNH ẢNH GỐC / BẢN GHÉP v8.1
  // =========================================================================
  window.toggleCompareOrig = function () {
    var img = document.getElementById("mainPreviewImg");
    var btn = document.getElementById("btnCompareToggle");
    window.showingOrigCompare = !window.showingOrigCompare;
    if (window.showingOrigCompare) {
      if (img) img.src = "icons/preview_orig.jpg";
      if (btn) btn.textContent = "✨ Xem Bản Ghép v8.1";
      var tEl = document.getElementById("previewTitle");
      if (tEl) tEl.textContent = "Ảnh Gốc Chưa Ghép (PWD05627.jpg)";
      window.showToast("Đang xem ảnh gốc chưa ghép");
    } else {
      if (img) img.src = window.currentMasterPreviewSrc;
      if (btn) btn.textContent = "👁 So Sánh Gốc";
      var meta = PRESET_META[window.currentPresetId];
      if (meta && document.getElementById("previewTitle")) {
        document.getElementById("previewTitle").textContent = meta.title;
      }
      window.showToast("Đang xem bản ghép v8.1 Master");
    }
  };

  // =========================================================================
  // 3. TÙY CHỌN CÔNG TẮC (SKIN SHIELD & LIGHT WRAP)
  // =========================================================================
  window.toggleOption = function (key) {
    if (key === "skinShield") {
      window.optSkinShield = !window.optSkinShield;
      var el = document.getElementById("swSkinShield");
      if (el) el.className = window.optSkinShield ? "switch-track active" : "switch-track";
      window.showToast("Skin Shield v8.1: " + (window.optSkinShield ? "BẬT" : "TẮT"));
    } else if (key === "catchlight") {
      window.optCatchlight = !window.optCatchlight;
      var el2 = document.getElementById("swCatchlight");
      if (el2) el2.className = window.optCatchlight ? "switch-track active" : "switch-track";
      window.showToast("Quầng sáng viền 360°: " + (window.optCatchlight ? "BẬT" : "TẮT"));
    }
  };

  // =========================================================================
  // 4. CHỌN CỰ LY CHỤP (SHOT FRAMING)
  // =========================================================================
  window.setFraming = function (type) {
    window.currentShotType = type;
    ["btnFullBody", "btnHalfBody", "btnPortrait"].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.className = "seg-item";
    });
    var hint = document.getElementById("framingHint");

    if (type === "full_body") {
      var fb = document.getElementById("btnFullBody");
      if (fb) fb.className = "seg-item active";
      if (hint) hint.textContent = "Bóng sàn 3D & Tiền cảnh f/1.8";
      window.showToast("Đã chọn cự ly: Toàn Thân (Bóng sàn 3D)");
    } else if (type === "half_body") {
      var hb = document.getElementById("btnHalfBody");
      if (hb) hb.className = "seg-item active";
      if (hint) hint.textContent = "Xóa phông dịu f/2.0 ngang eo";
      window.showToast("Đã chọn cự ly: Bán Thân (Xóa phông f/2.0)");
    } else if (type === "portrait") {
      var pt = document.getElementById("btnPortrait");
      if (pt) pt.className = "seg-item active";
      if (hint) hint.textContent = "Bokeh Fine-Art chân dung";
      window.showToast("Đã chọn cự ly: Chân Dung Fine-Art");
    }
  };

  // =========================================================================
  // 5. NẠP ĐỘNG VÀ CHỌN BỐI CẢNH TRONG KHO (STUDIO VAULT)
  // =========================================================================
  window.loadPresets = async function () {
    var vaultGrid = document.getElementById("vaultGrid");
    if (!vaultGrid) return;

    try {
      var res = await fetch(API_BASE + "/api/presets", { cache: "no-store" });
      var presets = await res.json();
      if (!Array.isArray(presets) || presets.length === 0) return;

      var foundActive = false;
      var html = "";

      presets.forEach(function (p) {
        var pid = p.id;
        var pTitle = p.title || p.name || pid;
        var pThumb = p.thumb_url ? (p.thumb_url.indexOf("http") === 0 ? p.thumb_url : API_BASE + p.thumb_url) : "icons/thumb_korean_v8.jpg";
        var pPreview = p.clean_bg_url ? (p.clean_bg_url.indexOf("http") === 0 ? p.clean_bg_url : API_BASE + p.clean_bg_url) : (p.preview || pThumb);
        var pTag = p.tag || p.category || "STUDIO";
        var pSub = p.sub || p.tone || ("Hướng sáng " + (p.light_dir || "tự nhiên"));

        PRESET_META[pid] = {
          title: pTitle,
          preview: pPreview,
          thumb: pThumb,
          tag: pTag,
          sub: pSub,
          floorHex: p.floorHex || "#E2D5C1",
          wallHex: p.wallHex || "#EFE5D4",
          flowerHex: p.flowerHex || "#F7F2E7",
          fg: p.fg || "Mặt sàn tiếp đất tự nhiên kèm bóng đổ 3D.",
          mid: p.mid || "Khóa cứng 100% độ nét pixel gốc Dâu Rể 33MP (Zero-Halo).",
          bg: p.bg || "Bối cảnh chuẩn Studio hòa sắc quang học toàn diện."
        };

        var isActive = (pid === window.currentPresetId);
        if (isActive) foundActive = true;

        var tagStyle = "";
        var tagLower = pTag.toLowerCase();
        if (tagLower.indexOf("lux") >= 0 || tagLower.indexOf("châu âu") >= 0) {
          tagStyle = ' style="background-color: #d97706;"';
        } else if (tagLower.indexOf("clas") >= 0 || tagLower.indexOf("cổ điển") >= 0) {
          tagStyle = ' style="background-color: #7c3aed;"';
        } else if (tagLower.indexOf("chân dung") >= 0 || tagLower.indexOf("mỹ thuật") >= 0) {
          tagStyle = ' style="background-color: #059669;"';
        }

        html += '<div role="button" id="preset_' + pid + '" class="vault-item' + (isActive ? ' active' : '') + '" data-preset="' + pid + '">' +
          '<div class="vault-thumb-box">' +
            '<img src="' + pThumb + '" alt="' + pTitle + '">' +
            '<span class="vault-tag"' + tagStyle + '>' + pTag + '</span>' +
          '</div>' +
          '<div class="vault-item-title">' + pTitle + '</div>' +
          '<div class="vault-item-sub">' + pSub + '</div>' +
        '</div>';
      });

      vaultGrid.innerHTML = html;

      if (!foundActive && presets.length > 0) {
        window.currentPresetId = presets[0].id;
      }

      if (PRESET_META[window.currentPresetId]) {
        var curMeta = PRESET_META[window.currentPresetId];
        window.currentMasterPreviewSrc = curMeta.preview;
        var pImg = document.getElementById("mainPreviewImg");
        if (pImg && !window.showingOrigCompare && !window.uploadedBgFile) {
          pImg.src = curMeta.preview;
        }
        var pTitleEl = document.getElementById("previewTitle");
        if (pTitleEl && !window.showingOrigCompare && !window.uploadedBgFile) {
          pTitleEl.textContent = curMeta.title;
        }
      }
    } catch (e) {
      console.warn("[NenAI] Lỗi nạp danh sách presets:", e);
    }
  };

  window.selectPreset = function (id) {
    window.currentPresetId = id;
    window.uploadedBgFile = null;
    window.uploadedBgPath = null;
    window.uploadedBgName = null;
    window.showingOrigCompare = false;
    var cmpBtn = document.getElementById("btnCompareToggle");
    if (cmpBtn) cmpBtn.textContent = "👁 So Sánh Gốc";

    var allVaultItems = document.querySelectorAll("#vaultGrid .vault-item, .vault-item");
    allVaultItems.forEach(function (el) {
      var pId = el.getAttribute("data-preset") || (el.id ? el.id.replace("preset_", "") : null);
      if (pId === id) {
        el.className = "vault-item active";
      } else {
        el.className = "vault-item";
      }
    });

    var meta = PRESET_META[id];
    if (meta) {
      window.currentMasterPreviewSrc = meta.preview;
      var img = document.getElementById("mainPreviewImg");
      if (img) img.src = meta.preview;
      var title = document.getElementById("previewTitle");
      if (title) title.textContent = meta.title;

      var sf = document.getElementById("swatchFloor");
      if (sf) sf.style.backgroundColor = meta.floorHex;
      var hf = document.getElementById("hexFloor");
      if (hf) hf.textContent = meta.floorHex;

      var sw = document.getElementById("swatchWall");
      if (sw) sw.style.backgroundColor = meta.wallHex;
      var hw = document.getElementById("hexWall");
      if (hw) hw.textContent = meta.wallHex;

      var sfl = document.getElementById("swatchFlower");
      if (sfl) sfl.style.backgroundColor = meta.flowerHex;
      var hfl = document.getElementById("hexFlower");
      if (hfl) hfl.textContent = meta.flowerHex;

      var dfg = document.getElementById("descForeground");
      if (dfg) dfg.textContent = meta.fg;
      var dmg = document.getElementById("descMidground");
      if (dmg) dmg.textContent = meta.mid;
      var dbg = document.getElementById("descBackground");
      if (dbg) dbg.textContent = meta.bg;

      window.showToast("Đã chọn: " + meta.title);
    }
  };

  // =========================================================================
  // 6. CHỌN BO VIỀN TRIỂN LÃM (PASSE-PARTOUT)
  // =========================================================================
  window.setMat = function (color) {
    window.currentMat = color;
    ["matNone", "matWhite", "matCream"].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.className = "mat-pill";
    });
    if (color === "none") {
      var m0 = document.getElementById("matNone");
      if (m0) m0.className = "mat-pill active";
      window.showToast("Bo viền: Không bo");
    } else if (color === "white") {
      var m1 = document.getElementById("matWhite");
      if (m1) m1.className = "mat-pill active";
      window.showToast("Bo viền: Viền trắng");
    } else if (color === "cream") {
      var m2 = document.getElementById("matCream");
      if (m2) m2.className = "mat-pill active";
      window.showToast("Bo viền: Trắng ngà");
    }
  };

  // =========================================================================
  // 7. QUY TRÌNH 1-CLICK: TÁCH NỀN -> ĐỒNG BỘ CIE LAB -> ĐẨY VÀO PHOTOSHOP
  // =========================================================================
  window.handleOneClickPipeline = async function () {
    var btn = document.getElementById("btnPushPhotoshop");
    if (!btn) return;
    var oldText = btn.innerHTML;
    btn.innerHTML = "<span>⏳ ĐANG ĐỒNG BỘ CIE LAB &amp; ĐẨY VÀO PHOTOSHOP...</span>";
    btn.className = "cta-gold-btn disabled";

    try {
      var formData = new FormData();
      if (window.uploadedBgFile) {
        formData.append("bg_file", window.uploadedBgFile);
      } else if (window.uploadedBgPath) {
        formData.append("reference_path", window.uploadedBgPath);
      } else {
        formData.append("preset_id", window.currentPresetId);
      }
      formData.append("shot_type", window.currentShotType);
      formData.append("passe_partout", window.currentMat);
      formData.append("skin_shield", window.optSkinShield);

      var resProcess = await fetch(API_BASE + "/api/process", {
        method: "POST",
        body: formData
      });
      var dataProcess = await resProcess.json();

      if (!dataProcess.success) {
        throw new Error(dataProcess.detail || "Không thể xử lý ảnh.");
      }

      var masterUrl = dataProcess.urls.master || dataProcess.urls.v1;
      window.currentMasterPreviewSrc = API_BASE + masterUrl + "?t=" + Date.now();
      var img = document.getElementById("mainPreviewImg");
      if (img) img.src = window.currentMasterPreviewSrc;

      var resPush = await fetch(API_BASE + "/api/photoshop/push", { method: "POST" });
      var dataPush = await resPush.json();

      if (dataPush.success) {
        window.showToast("✨ Đã xuất 5 Layer 33MP vào Photoshop (" + dataProcess.total_time + "s)!", "success");
      } else {
        window.showToast("✨ Đã tạo Bản Master 33MP (" + dataProcess.total_time + "s)!", "success");
      }
    } catch (err) {
      window.showToast(err.message || "Lỗi kết nối Backend", "error");
    } finally {
      btn.innerHTML = oldText;
      btn.className = "cta-gold-btn";
    }
  };

  // =========================================================================
  // 8. TINH CHỈNH ÁNH SÁNG (REGENERATE VARIATION)
  // =========================================================================
  window.handleRegenerate = async function () {
    var btn = document.getElementById("btnRegen");
    if (!btn) return;
    var oldHtml = btn.innerHTML;
    btn.innerHTML = "<span>⏳ Đang tinh chỉnh...</span>";

    try {
      var formData = new FormData();
      formData.append("shot_type", window.currentShotType);
      formData.append("passe_partout", window.currentMat);

      var res = await fetch(API_BASE + "/api/regenerate", {
        method: "POST",
        body: formData
      });
      var data = await res.json();

      if (data.success) {
        var masterUrl = data.urls.master || data.urls.v1;
        window.currentMasterPreviewSrc = API_BASE + masterUrl + "?t=" + Date.now();
        var img = document.getElementById("mainPreviewImg");
        if (img) img.src = window.currentMasterPreviewSrc;

        await fetch(API_BASE + "/api/photoshop/push", { method: "POST" });
        window.showToast("🔄 Đã cập nhật biến thể ánh sáng mới vào Photoshop!");
      } else {
        throw new Error(data.detail || "Không thể tạo lại.");
      }
    } catch (err) {
      window.showToast(err.message || "Vui lòng chạy ghép 1-Click trước.", "error");
    } finally {
      btn.innerHTML = oldHtml;
    }
  };

  // =========================================================================
  // 9. NẠP ẢNH MẪU TỰ CHỌN (HỖ TRỢ ADOBE UXP NATIVE & WEB BROWSER)
  // =========================================================================
  window.updateSceneBreakdownUI = function (bd, cp) {
    if (!bd && !cp) return;
    if (cp) {
      if (cp.floor_hex) {
        var sf = document.getElementById("swatchFloor");
        if (sf) sf.style.backgroundColor = cp.floor_hex;
        var hf = document.getElementById("hexFloor");
        if (hf) hf.textContent = cp.floor_hex;
      }
      if (cp.wall_hex) {
        var sw = document.getElementById("swatchWall");
        if (sw) sw.style.backgroundColor = cp.wall_hex;
        var hw = document.getElementById("hexWall");
        if (hw) hw.textContent = cp.wall_hex;
      }
      if (cp.flower_hex) {
        var sfl = document.getElementById("swatchFlower");
        if (sfl) sfl.style.backgroundColor = cp.flower_hex;
        var hfl = document.getElementById("hexFlower");
        if (hfl) hfl.textContent = cp.flower_hex;
      }
    }
    if (bd) {
      if (bd.tien_canh) {
        var dfg = document.getElementById("descForeground");
        if (dfg) dfg.textContent = (bd.tien_canh.mat_san || "") + " " + (bd.tien_canh.cum_hoa_sat_san || "");
      }
      if (bd.trung_canh) {
        var dmg = document.getElementById("descMidground");
        if (dmg) dmg.textContent = (bd.trung_canh.vom_hoa || "") + " " + (bd.trung_canh.khoang_trong_nhan_vat || "");
      }
      if (bd.hau_canh_va_nen) {
        var dbg = document.getElementById("descBackground");
        if (dbg) dbg.textContent = (bd.hau_canh_va_nen.tuong_nen || "") + " " + (bd.hau_canh_va_nen.anh_sang || "");
      }
    }
  };

  window.processSelectedBgPath = async function (filePath, fileName) {
    window.showToast("Đang đọc & phân tích bối cảnh: " + fileName + "...");

    var pTitleEl = document.getElementById("previewTitle");
    if (pTitleEl) pTitleEl.textContent = "Bối Cảnh Mẫu: " + fileName;

    var allVaultItems = document.querySelectorAll("#vaultGrid .vault-item, .vault-item");
    allVaultItems.forEach(function (el) { el.classList.remove("active"); });

    var analyzeForm = new FormData();
    analyzeForm.append("reference_path", filePath);

    try {
      var resAnalyze = await fetch(API_BASE + "/api/scene/analyze", {
        method: "POST",
        body: analyzeForm
      });
      var dataAnalyze = await resAnalyze.json();

      if (dataAnalyze.success) {
        if (dataAnalyze.preview_url) {
          var previewSrc = API_BASE + dataAnalyze.preview_url + "?t=" + Date.now();
          window.currentMasterPreviewSrc = previewSrc;
          var pImg = document.getElementById("mainPreviewImg");
          if (pImg) pImg.src = previewSrc;
        }

        if (dataAnalyze.breakdown || dataAnalyze.color_palette) {
          window.updateSceneBreakdownUI(dataAnalyze.breakdown, dataAnalyze.color_palette);
        }
        window.showToast("✨ Đã nạp thành công bối cảnh mẫu: " + fileName + "!", "success");
      } else {
        window.showToast("Không thể phân tích bối cảnh mẫu.", "error");
      }
    } catch (e) {
      console.error("[NenAI] Lỗi phân tích bối cảnh:", e);
      window.showToast(e.message || "Lỗi đọc ảnh mẫu", "error");
    }
  };

  window.processSelectedBgFile = async function (file, fileName) {
    window.showToast("Đang nạp & phân tích bối cảnh: " + fileName + "...");

    var pTitleEl = document.getElementById("previewTitle");
    if (pTitleEl) pTitleEl.textContent = "Bối Cảnh Mẫu: " + fileName;

    var allVaultItems = document.querySelectorAll("#vaultGrid .vault-item, .vault-item");
    allVaultItems.forEach(function (el) { el.classList.remove("active"); });

    var analyzeForm = new FormData();
    analyzeForm.append("bg_file", file, fileName);

    try {
      var resAnalyze = await fetch(API_BASE + "/api/scene/analyze", {
        method: "POST",
        body: analyzeForm
      });
      var dataAnalyze = await resAnalyze.json();

      if (dataAnalyze.success) {
        if (dataAnalyze.preview_url) {
          var previewSrc = API_BASE + dataAnalyze.preview_url + "?t=" + Date.now();
          window.currentMasterPreviewSrc = previewSrc;
          var pImg = document.getElementById("mainPreviewImg");
          if (pImg) pImg.src = previewSrc;
        }

        if (dataAnalyze.breakdown || dataAnalyze.color_palette) {
          window.updateSceneBreakdownUI(dataAnalyze.breakdown, dataAnalyze.color_palette);
        }
        window.showToast("✨ Đã nạp thành công bối cảnh mẫu: " + fileName + "!", "success");
      } else {
        window.showToast("Không thể phân tích bối cảnh mẫu.", "error");
      }
    } catch (e) {
      console.error("[NenAI] Lỗi phân tích bối cảnh:", e);
      window.showToast(e.message || "Lỗi đọc ảnh mẫu", "error");
    }
  };

  window.pickAndUploadBg = async function () {
    console.log("[NenAI] Bắt đầu kích hoạt mở file bối cảnh mẫu...");

    // 1. Kiểm tra môi trường Adobe Photoshop UXP
    var uxp = null;
    try {
      if (typeof require === "function") {
        uxp = require("uxp");
      }
    } catch (eUxp) {
      console.warn("[NenAI] Không chạy require('uxp'):", eUxp);
    }

    if (uxp && uxp.storage && uxp.storage.localFileSystem) {
      try {
        var fs = uxp.storage.localFileSystem;
        var fileEntry = await fs.getFileForOpening({
          types: ["jpg", "jpeg", "png", "webp", "tif", "tiff"]
        });

        if (!fileEntry) {
          console.log("[NenAI] Người dùng hủy hộp thoại chọn file.");
          return;
        }

        var filePath = fileEntry.nativePath || "";
        var fileName = fileEntry.name || "bối_cảnh_mẫu.jpg";
        console.log("[NenAI UXP] Đã chọn file:", fileName, "đường dẫn:", filePath);

        window.uploadedBgPath = filePath;
        window.uploadedBgName = fileName;
        window.uploadedBgFile = null;

        if (filePath) {
          await window.processSelectedBgPath(filePath, fileName);
          return;
        }

        // Fallback đọc dạng binary nếu nativePath không có
        var arrBuf = await fileEntry.read({ format: uxp.storage.formats.binary });
        var mime = fileName.toLowerCase().endsWith(".png") ? "image/png" : "image/jpeg";
        var blob = new Blob([arrBuf], { type: mime });
        window.uploadedBgFile = blob;
        await window.processSelectedBgFile(blob, fileName);
        return;
      } catch (errPicker) {
        console.error("[NenAI UXP] Lỗi mở UXP File Picker:", errPicker);
        window.showToast("Lỗi mở hộp thoại chọn file: " + errPicker.message, "error");
        return;
      }
    }

    // 2. Môi trường Trình Duyệt Web (Fallback)
    console.log("[NenAI] Đang chạy trên trình duyệt web, kích hoạt <input type='file'>");
    var inp = document.getElementById("uploadBgInput");
    if (inp) {
      inp.value = "";
      inp.click();
    } else {
      window.showToast("Không tìm thấy bộ chọn file.", "error");
    }
  };

  window.handleBgUpload = async function (input) {
    if (!input || !input.files || input.files.length === 0) return;
    var file = input.files[0];
    window.uploadedBgFile = file;
    window.uploadedBgPath = null;
    window.uploadedBgName = file.name;
    await window.processSelectedBgFile(file, file.name);
  };

  // =========================================================================
  // 10. LƯU BỐI CẢNH VÀO KHO
  // =========================================================================
  window.handleSavePreset = async function () {
    var name = prompt("Đặt tên cho bối cảnh này để lưu vào kho:", "Mẫu Cưới Studio Mới");
    if (!name) return;

    var cat = prompt("Thể loại (Studio Hàn Quốc / Châu Âu / Cổ Điển / Chân Dung / Ngoại Cảnh):", "Studio Hàn Quốc") || "Studio";

    var formData = new FormData();
    formData.append("name", name);
    formData.append("category", cat);
    if (window.uploadedBgFile) {
      formData.append("bg_file", window.uploadedBgFile);
    } else if (window.uploadedBgPath) {
      formData.append("reference_path", window.uploadedBgPath);
    }

    try {
      var res = await fetch(API_BASE + "/api/presets/save", {
        method: "POST",
        body: formData
      });
      var data = await res.json();
      if (data.success && data.preset) {
        window.showToast("💾 Đã lưu \"" + name + "\" vào Kho Bối Cảnh!");
        await window.loadPresets();
        window.selectPreset(data.preset.id);
      } else {
        window.showToast(data.detail || "Không thể lưu mẫu.", "error");
      }
    } catch (e) {
      window.showToast(e.message, "error");
    }
  };

  // =========================================================================
  // 11. KIỂM TRA TÀI LIỆU PHOTOSHOP & TRẠNG THÁI ENGINE
  // =========================================================================
  window.checkPhotoshopConnection = async function () {
    var docLabel = document.getElementById("psDocStatus");
    var statusText = document.getElementById("psStatusText");
    var badge = document.getElementById("psStatusBadge");
    if (!docLabel || !statusText || !badge) return;

    try {
      var res = await fetch(API_BASE + "/api/photoshop/status", { cache: "no-store" });
      var data = await res.json();

      if (data.ui_hash) {
        if (window.__NENAI_UI_HASH && window.__NENAI_UI_HASH !== data.ui_hash) {
          if (typeof window.hotReloadPanelUI === "function") {
            window.hotReloadPanelUI(false);
            return;
          }
        }
        window.__NENAI_UI_HASH = data.ui_hash;
      }

      if (data.connected && data.doc) {
        var doc = data.doc;
        var w = doc.width ? parseInt(doc.width) : 4672;
        var h = doc.height ? parseInt(doc.height) : 7008;
        docLabel.textContent = "Đang mở: " + doc.name + " (" + w + " × " + h + " px)";
        docLabel.style.color = "#34d399";
        statusText.textContent = "Đã Kết Nối PS";
        badge.style.borderColor = "rgba(16, 185, 129, 0.45)";
        var resEl = document.getElementById("previewRes");
        if (resEl) resEl.textContent = w + " × " + h + " (33MP)";
      } else {
        docLabel.textContent = "Backend v8.1 Online · Sẵn sàng xử lý 33MP";
        docLabel.style.color = "#34d399";
        statusText.textContent = "Engine Online";
        badge.style.borderColor = "rgba(16, 185, 129, 0.4)";
      }
    } catch (e) {
      docLabel.textContent = "Chế độ Xem Nhanh · Bấm 🔄 Cập nhật hoặc 1-Click";
      docLabel.style.color = "#f3cf6e";
      statusText.textContent = "Photoshop 2026";
    }
  };
  window.pollHealth = window.checkPhotoshopConnection;

  // =========================================================================
  // 12. BỘ ĐIỀU PHỐI SỰ KIỆN TOÀN CỤC (EVENT DELEGATION CHO ADOBE UXP)
  // Bắt mọi thao tác click/tap trên toàn bộ Panel, KHÔNG phụ thuộc vào inline onclick!
  // =========================================================================
  function handlePanelClick(e) {
    if (!e || !e.target) return;
    var target = e.target;

    // 1. Icon Logo (N)
    var brandIcon = target.closest("#brandIconLogo, .brand-icon");
    if (brandIcon) {
      e.preventDefault();
      if (typeof window.hotReloadPanelUI === "function") {
        window.hotReloadPanelUI(true);
      } else {
        window.location.reload();
      }
      return;
    }

    // 2. Nút 🔄 Cập nhật
    var btnReload = target.closest("#btnHotReloadUI, .btn-hot-reload");
    if (btnReload) {
      e.preventDefault();
      if (typeof window.hotReloadPanelUI === "function") {
        window.hotReloadPanelUI(true);
      } else {
        window.location.reload();
      }
      return;
    }

    // 3. Nút 👁 So Sánh Gốc
    var btnCompare = target.closest("#btnCompareToggle, .btn-compare-pill");
    if (btnCompare) {
      e.preventDefault();
      window.toggleCompareOrig();
      return;
    }

    // 4. Cự Ly Chụp (Shot Framing buttons)
    var segItem = target.closest(".seg-item");
    if (segItem) {
      e.preventDefault();
      var fType = segItem.getAttribute("data-framing") || (
        segItem.id === "btnFullBody" ? "full_body" :
        segItem.id === "btnHalfBody" ? "half_body" :
        segItem.id === "btnPortrait" ? "portrait" : null
      );
      if (fType) {
        window.setFraming(fType);
      }
      return;
    }

    // 5. Nút + Nạp Ảnh Mẫu
    var btnUpload = target.closest("#btnUploadBg, .btn-upload-pill");
    if (btnUpload) {
      e.preventDefault();
      window.pickAndUploadBg();
      return;
    }

    // 6. Kho Bối Cảnh Mẫu (Studio Vault cards)
    var vaultItem = target.closest(".vault-item");
    if (vaultItem) {
      e.preventDefault();
      var pId = vaultItem.getAttribute("data-preset") || (
        vaultItem.id ? vaultItem.id.replace("preset_", "") : null
      );
      if (pId) {
        window.selectPreset(pId);
      }
      return;
    }

    // 7. Công tắc gạt (Toggle rows)
    var toggleRow = target.closest(".toggle-row");
    if (toggleRow) {
      e.preventDefault();
      var tKey = toggleRow.getAttribute("data-toggle") || (
        toggleRow.id === "toggleRowSkinShield" ? "skinShield" :
        toggleRow.id === "toggleRowCatchlight" ? "catchlight" : null
      );
      if (tKey) {
        window.toggleOption(tKey);
      }
      return;
    }

    // 8. Bo Viền Triển Lãm (Mat pills)
    var matPill = target.closest(".mat-pill");
    if (matPill) {
      e.preventDefault();
      var mColor = matPill.getAttribute("data-mat") || (
        matPill.id === "matNone" ? "none" :
        matPill.id === "matWhite" ? "white" :
        matPill.id === "matCream" ? "cream" : null
      );
      if (mColor) {
        window.setMat(mColor);
      }
      return;
    }

    // 9. Nút chính: ⚡ ĐẨY BẢN MASTER 33MP VÀO PHOTOSHOP
    var btnPush = target.closest("#btnPushPhotoshop, .cta-gold-btn");
    if (btnPush) {
      e.preventDefault();
      if (!btnPush.classList.contains("disabled")) {
        window.handleOneClickPipeline();
      }
      return;
    }

    // 10. Nút phụ: 🔄 Tinh Chỉnh Ánh Sáng
    var btnRegen = target.closest("#btnRegen");
    if (btnRegen) {
      e.preventDefault();
      window.handleRegenerate();
      return;
    }

    // 11. Nút phụ: 💾 Lưu Bối Cảnh Vào Kho
    var btnSave = target.closest("#btnSavePreset, #btnSavePresetVault, .btn-save-pill");
    if (btnSave) {
      e.preventDefault();
      window.handleSavePreset();
      return;
    }
  }

  // Gắn bộ lắng nghe sự kiện trên cả document và window với cả click và pointerdown
  document.addEventListener("click", handlePanelClick, true);
  document.addEventListener("pointerdown", function (e) {
    // Kích hoạt hiệu ứng visual phản hồi ngay khi chạm
    var btn = e.target.closest(".cta-gold-btn, .sub-action-btn, .seg-item, .vault-item, .mat-pill, .btn-hot-reload, .btn-compare-pill, .btn-upload-pill");
    if (btn) {
      btn.style.transform = "scale(0.97)";
      setTimeout(function () {
        btn.style.transform = "";
      }, 150);
    }
  }, true);

  // Lắng nghe file input change
  function attachFileInputListener() {
    var inp = document.getElementById("uploadBgInput");
    if (inp && !inp.__nenai_bound) {
      inp.__nenai_bound = true;
      inp.addEventListener("change", function () {
        window.handleBgUpload(this);
      });
    }
  }

  // Khởi động khi DOM sẵn sàng
  function initController() {
    console.log("[NenAI Controller] DOM Ready — Đăng ký kết nối và nạp danh sách kho mẫu");
    attachFileInputListener();
    window.loadPresets();
    window.checkPhotoshopConnection();
    if (window.__NENAI_POLL_TIMER) clearInterval(window.__NENAI_POLL_TIMER);
    window.__NENAI_POLL_TIMER = setInterval(window.checkPhotoshopConnection, 3000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initController);
  } else {
    initController();
  }

  window.__initNenAIController = initController;
})();
