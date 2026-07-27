// HAKON 智能剧本处理系统 —— 前端逻辑

const $ = (id) => document.getElementById(id);

// ════════ 暗语门禁 ════════
const GATE_PASSWORD = "畅索";

function initGate() {
  const gate = $("gate-screen");
  const input = $("gate-input");
  const submit = $("gate-submit");
  const error = $("gate-error");

  // 如果 sessionStorage 已通过验证，直接跳过门禁
  if (sessionStorage.getItem("hakon_gate_passed") === "1") {
    gate.style.display = "none";
    enterApp();
    return;
  }

  input.focus();

  function tryEnter() {
    const val = input.value.trim();
    if (val === GATE_PASSWORD) {
      sessionStorage.setItem("hakon_gate_passed", "1");
      error.textContent = "";
      gate.classList.add("fade-out");
      setTimeout(() => {
        gate.style.display = "none";
        enterApp();
      }, 600);
    } else {
      error.textContent = "暗语不正确，请重试";
      input.value = "";
      input.focus();
    }
  }
  submit.addEventListener("click", tryEnter);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") tryEnter();
  });
}

function enterApp() {
  $("app-main").classList.remove("hidden");
}

// 生成飘雪动画
function generateSnow() {
  const container = $("gate-snow");
  if (!container) return;
  const flakes = ["❄", "❅", "❆", "·", "•"];
  for (let i = 0; i < 30; i++) {
    const s = document.createElement("span");
    s.textContent = flakes[Math.floor(Math.random() * flakes.length)];
    s.style.left = Math.random() * 100 + "%";
    s.style.fontSize = (8 + Math.random() * 16) + "px";
    s.style.animationDuration = (8 + Math.random() * 12) + "s";
    s.style.animationDelay = (Math.random() * 10) + "s";
    s.style.opacity = 0.3 + Math.random() * 0.5;
    container.appendChild(s);
  }
}

// 启动
initGate();
generateSnow();

const MODE_CONFIG = {
  normal: {
    stepLabels: {
      step1: "剧本理解与风格分析",
      step2: "人物动作与情绪增强",
      step3: "镜头切分",
      step4: "分镜设计与镜头语言",
    },
    btnText: "生成分镜",
    emptyTitle: "分镜将显示在这里",
    emptyHint: "填入剧本，点击「生成分镜」",
    inputLabel: "原始剧本（AI 会自动分析风格并改编）",
    exportWord: true,
    videoPrompt: true,
  },
  pro: {
    stepLabels: {
      step1: "剧本理解与风格分析",
      step2: "人物动作与情绪增强",
      step3: "镜头切分",
      step4: "五层电影感 Prompt 设计",
    },
    btnText: "生成专业分镜",
    emptyTitle: "专业分镜将显示在这里",
    emptyHint: "填入剧本，点击「生成专业分镜」",
    inputLabel: "原始剧本（专业模式将输出中英对照的完整 AI 视频 Prompt）",
    exportWord: true,
    videoPrompt: true,
  },
  narration: {
    stepLabels: {
      step1: "识别旁白与可视觉化信息",
      step2: "旁白类型分类与转化策略",
      step3: "五层法改写每个场景",
      step4: "对白还原与一致性检查",
    },
    btnText: "改写为视觉化剧本",
    emptyTitle: "改写后的纯视觉化剧本将显示在这里",
    emptyHint: "粘贴含大量旁白的剧本，点击「改写为视觉化剧本」",
    inputLabel: "含旁白的原始剧本（AI 会删除所有旁白，转化为纯视觉化描写）",
    exportWord: false,
    videoPrompt: false,
  },
};

function getMode() {
  return document.querySelector('input[name="mode"]:checked').value;
}

function applyModeUI(mode) {
  const cfg = MODE_CONFIG[mode];
  $("generate-btn").textContent = cfg.btnText;
  $("empty-text").textContent = cfg.emptyTitle;
  $("empty-hint").textContent = cfg.emptyHint;
  $("input-label").textContent = cfg.inputLabel;
}

// 模式切换
document.querySelectorAll('input[name="mode"]').forEach(input => {
  input.addEventListener("change", (e) => {
    document.querySelectorAll(".mode-tab").forEach(t => t.classList.remove("active"));
    e.target.closest(".mode-tab").classList.add("active");
    applyModeUI(e.target.value);
  });
});

$("generate-btn").addEventListener("click", () => generate());

async function generate() {
  const script = $("script").value.trim();
  if (script.length < 10) {
    alert("请输入至少 10 个字符的剧本内容。");
    return;
  }

  const mode = getMode();
  const payload = { script, mode };
  const cfg = MODE_CONFIG[mode];

  $("generate-btn").disabled = true;
  $("generate-btn").textContent = "生成中…";
  $("empty-state").classList.add("hidden");
  $("result-area").classList.add("hidden");
  $("progress-area").classList.remove("hidden");
  $("progress-list").innerHTML = "";

  const startedSteps = new Set();

  try {
    const resp = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) throw new Error(await resp.text());

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let resultData = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop();
      for (const block of blocks) {
        const evt = parseSSEBlock(block);
        if (!evt) continue;
        handleEvent(evt, mode, startedSteps, (d) => { resultData = d; });
      }
    }
    if (resultData) {
      renderResult(resultData);
      // 生成成功后清空左侧剧本输入框，优化动线
      $("script").value = "";
      $("script").blur();
    }
  } catch (e) {
    alert("生成失败：" + e.message);
    $("empty-state").classList.remove("hidden");
  } finally {
    $("generate-btn").disabled = false;
    $("generate-btn").textContent = cfg.btnText;
    $("progress-area").classList.add("hidden");
  }
}

function parseSSEBlock(block) {
  const lines = block.split("\n");
  let event = null, data = null;
  for (const line of lines) {
    if (line.startsWith("event: ")) event = line.slice(7).trim();
    else if (line.startsWith("data: ")) {
      const raw = line.slice(6);
      if (raw === "[DONE]") return { event: "done", data: null };
      try { data = JSON.parse(raw); } catch { data = raw; }
    }
  }
  return event ? { event, data } : null;
}

function handleEvent(evt, mode, startedSteps, onResult) {
  const labels = MODE_CONFIG[mode].stepLabels;
  if (evt.event === "start") {
    addProgress("step1", "开始处理剧本", "active");
  } else if (evt.event === "progress") {
    const { step, message } = evt.data;
    const order = ["step1", "step2", "step3", "step4"];
    const idx = order.indexOf(step);
    for (let i = 0; i < idx; i++) markProgressDone(order[i]);
    if (!startedSteps.has(step)) {
      startedSteps.add(step);
      addProgress(step, `${labels[step]}：${message}`, "active");
    } else {
      updateProgress(step, message);
    }
  } else if (evt.event === "result") {
    onResult(evt.data);
  } else if (evt.event === "complete") {
    markProgressDone("step4");
  } else if (evt.event === "error") {
    throw new Error(evt.data.message || "未知错误");
  }
}

function addProgress(step, text, status) {
  const li = document.createElement("li");
  li.id = "prog-" + step;
  li.className = status;
  li.innerHTML = `<span class="dot"></span><span class="text">${escapeHtml(text)}</span>`;
  $("progress-list").appendChild(li);
}
function updateProgress(step, text) {
  const li = $("prog-" + step);
  if (li) li.querySelector(".text").textContent = text;
}
function markProgressDone(step) {
  const li = $("prog-" + step);
  if (li) { li.classList.remove("active"); li.classList.add("done"); }
}

function renderResult(data) {
  $("progress-area").classList.add("hidden");
  $("result-area").classList.remove("hidden");
  const mode = data.mode || "normal";
  const cfg = MODE_CONFIG[mode];

  // 清空旧内容
  $("understanding-block").innerHTML = "";
  $("understanding-block").classList.add("hidden");
  $("scenes-container").innerHTML = "";
  $("video-prompt-section").classList.remove("hidden");
  $("prompt-preview").classList.add("hidden");
  $("convert-prompt-btn").classList.remove("hidden");
  $("export-word-btn").classList.remove("hidden");
  $("export-preview-word-btn").classList.add("hidden");

  if (mode === "narration") {
    renderNarrationResult(data);
    return;
  }

  const u = data.understanding;
  $("result-title").textContent = data.title || "未命名剧本";
  $("result-meta").textContent =
    `风格：${u.genre || "未知"} · 共 ${u.scenes.length} 场 / ${totalShots(data)} 镜`;

  // 剧本理解块
  $("understanding-block").classList.remove("hidden");
  $("understanding-block").innerHTML = `
    <h3>剧本理解 · AI 自动分析</h3>
    <div class="logline">「${escapeHtml(u.logline)}」</div>
    <div class="genre-tag">风格类型：${escapeHtml(u.genre || "未识别")}</div>
    <div class="tone">基调：${escapeHtml(u.tone || "—")}</div>
    <div class="relationships">${escapeHtml(u.relationships)}</div>
  `;

  // 场景与镜头
  const container = $("scenes-container");
  for (const scene of data.scenes) {
    const block = document.createElement("div");
    block.className = "scene-block";
    block.innerHTML = `
      <div class="scene-heading">
        <span class="scene-id">${escapeHtml(scene.scene_id)}</span>
        <span class="scene-title">${escapeHtml(scene.scene_heading)}</span>
        <span style="color:var(--text-dim);font-size:12px;margin-left:auto;">${scene.shots.length} 镜</span>
      </div>
      <div class="shots-grid"></div>
    `;
    const grid = block.querySelector(".shots-grid");
    for (const shot of scene.shots) {
      grid.appendChild(renderShotCard(shot));
    }
    container.appendChild(block);
  }

  // 导出按钮
  $("export-btn").onclick = () => exportJSON(data);
  $("export-word-btn").onclick = () => exportWord(data);

  let currentPromptText = "";
  $("convert-prompt-btn").onclick = () => convertToVideoPrompt(data);
  $("copy-prompt-btn").onclick = () => copyPrompt(currentPromptText);
  $("export-txt-btn").onclick = () => exportTxt(data, currentPromptText);
  $("export-preview-word-btn").onclick = () => exportWord(data);
  $("export-preview-word-btn").classList.remove("hidden");
  $("prompt-preview-title").textContent = "视频生成 Prompt（可直接复制使用）";

  function convertToVideoPrompt(data) {
    const btn = $("convert-prompt-btn");
    const preview = $("prompt-preview");
    if (!preview.classList.contains("hidden")) {
      preview.classList.add("hidden");
      btn.textContent = "▼ 转换为视频 Prompt";
      return;
    }
    btn.textContent = "转换中…";
    btn.disabled = true;
    fetch("/api/export/video-prompts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data }),
    }).then(r => { if (!r.ok) throw new Error("转换失败"); return r.text(); })
      .then(text => {
        currentPromptText = text;
        $("prompt-text").textContent = text;
        preview.classList.remove("hidden");
        btn.textContent = "▲ 收起视频 Prompt";
      })
      .catch(e => { alert(e.message); btn.textContent = "▼ 转换为视频 Prompt"; })
      .finally(() => { btn.disabled = false; });
  }
}

function renderNarrationResult(data) {
  $("result-title").textContent = "旁白视觉化改写剧本";
  $("result-meta").textContent = `共 ${data.rewritten_scenes.length} 个场景 · 已删除旁白并转化为纯视觉描写`;

  const container = $("scenes-container");
  for (const scene of data.rewritten_scenes) {
    container.appendChild(renderNarrationScene(scene));
  }

  // narration 模式：提供 Word/TXT/JSON 导出，隐藏视频 Prompt
  $("export-word-btn").classList.remove("hidden");
  $("convert-prompt-btn").classList.add("hidden");
  $("prompt-preview").classList.add("hidden");

  $("export-btn").onclick = () => exportJSON(data);
  $("export-word-btn").onclick = () => exportNarrationWord(data);

  let currentNarrationText = "";
  $("export-txt-btn").onclick = () => exportNarrationTxt(data, currentNarrationText);
  $("copy-prompt-btn").onclick = () => copyPrompt(currentNarrationText);
  $("export-preview-word-btn").onclick = () => exportNarrationWord(data);
  $("export-preview-word-btn").classList.remove("hidden");

  // 默认直接展开预览
  $("prompt-preview-title").textContent = "改写后的纯视觉化剧本";
  fetch("/api/export/narration", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data }),
  }).then(r => { if (!r.ok) throw new Error("导出失败"); return r.text(); })
    .then(text => {
      currentNarrationText = text;
      $("prompt-text").textContent = text;
      $("prompt-preview").classList.remove("hidden");
    })
    .catch(e => console.error(e));
}

function renderNarrationScene(scene) {
  const block = document.createElement("div");
  block.className = "narration-scene";
  let note = "";
  if (scene.note) {
    note = `<div class="narration-note">改写说明：${escapeHtml(scene.note)}</div>`;
  }
  block.innerHTML = `
    <div class="scene-heading">
      <span class="scene-id">${escapeHtml(scene.scene_id)}</span>
      <span class="scene-title">${escapeHtml(scene.scene_heading)}</span>
    </div>
    <div class="narration-body">${escapeHtml(scene.body || "").replace(/\\n/g, "<br>")}</div>
    ${note}
  `;
  return block;
}

function renderShotCard(shot) {
  const card = document.createElement("div");
  card.className = "shot-card";
  const dlgText = shot.dialogue && shot.dialogue.trim()
    ? `${escapeHtml(shot.speaker || "")}：「${escapeHtml(shot.dialogue)}」`
    : "";
  const isPro = shot.lens || shot.lighting || shot.full_prompt;
  let proFields = "";
  let fullPromptBlock = "";
  if (isPro) {
    proFields = `
      ${shot.lens ? shotRowPro("焦段", shot.lens) : ""}
      ${shot.aperture ? shotRowPro("光圈", shot.aperture) : ""}
      ${shot.lighting ? shotRowPro("布光", shot.lighting) : ""}
      ${shot.color_grade ? shotRowPro("调色", shot.color_grade) : ""}
      ${shot.atmosphere ? shotRowPro("氛围", shot.atmosphere) : ""}
      ${shot.style_ref ? shotRowPro("风格参考", shot.style_ref) : ""}
      ${shot.duration ? shotRowPro("时长", shot.duration) : ""}
    `;
    if (shot.full_prompt) {
      const zhBlock = shot.full_prompt_zh
        ? `<div class="full-prompt-zh"><span class="zh-label">中文对照</span>${escapeHtml(shot.full_prompt_zh)}</div>`
        : "";
      fullPromptBlock = `<div class="full-prompt-block"><div class="full-prompt-label">Full Prompt（五层公式 · 英文）</div>${escapeHtml(shot.full_prompt)}${zhBlock}</div>`;
    }
  }
  card.innerHTML = `
    <div class="shot-header">
      <span class="shot-id">${escapeHtml(shot.shot_id)}</span>
      <span class="shot-type-badge">${escapeHtml(shot.shot_type)}</span>
    </div>
    <div class="shot-body">
      ${shotRow("景别", shot.camera_angle)}
      ${shotRow("运镜", shot.camera_movement)}
      ${shotRow("主体", shot.main_subject)}
      ${shot.description ? shotRowFull("描述", shot.description) : ""}
      ${dlgText ? shotRow("台词", dlgText) : ""}
      ${shot.reaction ? shotRow("反应", shot.reaction) : ""}
      ${proFields}
      ${fullPromptBlock}
    </div>
  `;
  return card;
}
function shotRowPro(label, value) {
  if (!value) return "";
  return `<div class="shot-row"><span class="label pro">${label}</span><span class="value">${escapeHtml(value)}</span></div>`;
}

function shotRow(label, value) {
  if (!value) return "";
  return `<div class="shot-row"><span class="label">${label}</span><span class="value">${escapeHtml(value)}</span></div>`;
}

function shotRowFull(label, value) {
  if (!value) return "";
  return `<div class="shot-row shot-row-full"><span class="label">${label}</span><div class="value">${escapeHtml(value)}</div></div>`;
}

function totalShots(data) {
  return data.scenes.reduce((n, s) => n + s.shots.length, 0);
}

function exportJSON(data) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${data.title || "storyboard"}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

async function exportWord(data) {
  const btn = $("export-word-btn");
  const original = btn.textContent;
  btn.textContent = "生成中…";
  btn.disabled = true;
  try {
    const resp = await fetch("/api/export/word", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data }),
    });
    if (!resp.ok) throw new Error(await resp.text());
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${data.title || "storyboard"}_分镜报告.docx`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    alert("Word 导出失败：" + e.message);
  } finally {
    btn.textContent = original;
    btn.disabled = false;
  }
}

function copyPrompt(text) {
  if (!text) return;
  navigator.clipboard.writeText(text).then(() => {
    const btn = $("copy-prompt-btn");
    const orig = btn.textContent;
    btn.textContent = "已复制 ✓";
    setTimeout(() => (btn.textContent = orig), 1500);
  });
}

function exportTxt(data, currentPromptText) {
  if (!currentPromptText) return;
  const blob = new Blob([currentPromptText], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${data.title || "storyboard"}_视频Prompt.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

function exportNarrationTxt(data, currentNarrationText) {
  if (!currentNarrationText) return;
  const blob = new Blob([currentNarrationText], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${data.title || "storyboard"}_旁白视觉化剧本.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

async function exportNarrationWord(data) {
  const btn = $("export-word-btn");
  const original = btn.textContent;
  btn.textContent = "生成中…";
  btn.disabled = true;
  try {
    const resp = await fetch("/api/export/word", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data }),
    });
    if (!resp.ok) throw new Error(await resp.text());
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${data.title || "storyboard"}_旁白视觉化剧本.docx`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    alert("Word 导出失败：" + e.message);
  } finally {
    btn.textContent = original;
    btn.disabled = false;
  }
}

function escapeHtml(s) {
  if (s == null) return "";
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}
