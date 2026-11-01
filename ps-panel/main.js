/**
 * NenAI Studio v8.1 PRO — Photoshop 2026 UXP Panel Entrypoint & Live Hot-Reload Engine
 * Cho phép tự động cập nhật giao diện (HTML + CSS + JS) trực tiếp trong Photoshop
 * mà KHÔNG cần tắt hay mở lại Photoshop.
 */

window.__NENAI_UI_HASH = window.__NENAI_UI_HASH || "";
window.__NENAI_HOT_RELOADING = false;

function _parseRawHtmlBundle(rawHtml) {
  var cssMatch = rawHtml.match(/<style[^>]*>([\s\S]*?)<\/style>/i);
  var rootMatch = rawHtml.match(/<!--\s*NENAI_ROOT_START\s*-->([\s\S]*?)<!--\s*NENAI_ROOT_END\s*-->/i);
  var bodyMatch = rawHtml.match(/<body[^>]*>([\s\S]*?)<script/i);
  var scriptMatches = [];
  var re = /<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/gi;
  var m;
  while ((m = re.exec(rawHtml)) !== null) {
    scriptMatches.push(m[1]);
  }
  return {
    css: cssMatch ? cssMatch[1].trim() : "",
    body_html: rootMatch ? rootMatch[1].trim() : (bodyMatch ? bodyMatch[1].trim() : ""),
    js: scriptMatches.join("\n").trim()
  };
}

window.hotReloadPanelUI = async function(isManual) {
  if (window.__NENAI_HOT_RELOADING) return;
  window.__NENAI_HOT_RELOADING = true;

  var btn = document.getElementById("btnHotReloadUI");
  if (btn && isManual) {
    btn.textContent = "⏳ Đang nạp...";
  }

  try {
    var bundle = null;
    var apiBase = (window.location && window.location.origin && window.location.origin.indexOf("http") === 0)
      ? window.location.origin
      : "http://127.0.0.1:8989";

    // Cách 1: Nạp trực tiếp từ NenAI FastAPI Live Bundle Endpoint
    try {
      var res = await fetch(apiBase + "/api/ui/live?t=" + Date.now(), { cache: "no-store" });
      if (res.ok) {
        var data = await res.json();
        if (data && data.css && data.body_html) {
          bundle = data;
        }
      }
    } catch (eNet) {
      // Sẽ fallback sang đọc trực tiếp từ ổ cứng qua UXP LocalFileSystem
    }

    // Cách 2: Fallback đọc trực tiếp file index.html từ ổ cứng qua UXP Storage API
    if (!bundle) {
      try {
        if (typeof require === "function") {
          var uxp = require("uxp");
          var fs = uxp.storage.localFileSystem;
          var pluginFolder = await fs.getPluginFolder();
          var entry = await pluginFolder.getEntry("index.html");
          var rawHtml = await entry.read();
          if (rawHtml) {
            bundle = _parseRawHtmlBundle(rawHtml);
            bundle.ui_hash = "local_" + Date.now();
          }
        }
      } catch (eFs) {
        console.warn("[NenAI Hot-Reload] Fallback FS error:", eFs);
      }
    }

    if (!bundle || !bundle.body_html) {
      throw new Error("Không đọc được gói giao diện mới.");
    }

    // 1. Cập nhật CSS trực tiếp
    var styleEl = document.getElementById("nenaiMainStyle") || document.querySelector("style");
    if (styleEl && bundle.css) {
      styleEl.textContent = bundle.css;
    }

    // 2. Cập nhật HTML bên trong #nenaiAppRoot (hoặc body)
    var rootEl = document.getElementById("nenaiAppRoot");
    var cleanHtml = bundle.body_html;
    var innerMatch = cleanHtml.match(/<!--\s*NENAI_ROOT_START\s*-->([\s\S]*?)<!--\s*NENAI_ROOT_END\s*-->/i);
    if (innerMatch) {
      cleanHtml = innerMatch[1].trim();
    }
    if (rootEl) {
      rootEl.innerHTML = cleanHtml;
    }

    // 3. Lưu mã hash mới
    if (bundle.ui_hash) {
      window.__NENAI_UI_HASH = bundle.ui_hash;
    }

    // 4. Thực thi lại logic JS mới nếu có
    if (bundle.js) {
      try {
        var fn = new Function(bundle.js);
        fn();
      } catch (eEval) {
        console.warn("[NenAI Hot-Reload] JS re-init note:", eEval);
      }
    }

    if (typeof window.__initNenAIController === "function") {
      window.__initNenAIController();
    }

    if (typeof window.pollHealth === "function") {
      window.pollHealth();
    }

    if (typeof window.showToast === "function") {
      var timeStr = bundle.updated_at || new Date().toLocaleTimeString("vi-VN");
      window.showToast("✨ Đã cập nhật Panel trực tiếp (" + timeStr + ") — Không cần tắt mở PTS!", "success");
    }
  } catch (err) {
    if (typeof window.showToast === "function" && isManual) {
      window.showToast("Lỗi cập nhật UI: " + err.message, "error");
    }
  } finally {
    window.__NENAI_HOT_RELOADING = false;
    var btnAfter = document.getElementById("btnHotReloadUI");
    if (btnAfter) {
      btnAfter.textContent = "🔄 Cập nhật";
    }
  }
};

try {
  const { entrypoints } = require("uxp");
  entrypoints.setup({
    panels: {
      "com.nenai.studio.panel": {
        show() {
          console.log("[NenAI Studio] Panel hiển thị trong Photoshop 2026 — kiểm tra bản cập nhật UI...");
          if (typeof window.hotReloadPanelUI === "function") {
            window.hotReloadPanelUI(false);
          }
          if (typeof window.pollHealth === "function") {
            window.pollHealth();
          }
        }
      }
    }
  });
} catch (e) {
  // Chạy ngoài UXP (trên trình duyệt Web)
}
