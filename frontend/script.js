// نقطة نهاية الـ API — نفس المنشأ (الواجهة والـ API خلف نفس البروكسي)
const API_BASE = "/api";

const levelToClass = {
  "منخفضة": "low",
  "متوسطة": "medium",
  "مرتفعة": "high",
  "حرجة": "critical",
};
const levelColorVar = {
  low: "var(--low)", medium: "var(--medium)", high: "var(--high)", critical: "var(--critical)",
};

let lastSeenId = 0;
let firstLoad = true;

/* ============ أدوات مساعدة ============ */
function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
}

function safeParseArray(jsonStr) {
  try {
    const v = JSON.parse(jsonStr);
    return Array.isArray(v) ? v : [];
  } catch {
    return [];
  }
}

function openModal(id) { document.getElementById(id).hidden = false; }
function closeModal(id) { document.getElementById(id).hidden = true; }

/* ============ الإحصائيات ============ */
async function loadStats() {
  try {
    const res = await fetch(`${API_BASE}/stats`);
    const data = await res.json();
    const by = data.by_level || {};
    document.getElementById("statTotal").textContent = data.total || 0;
    document.getElementById("statLow").textContent = by["منخفضة"] || 0;
    document.getElementById("statMedium").textContent = by["متوسطة"] || 0;
    document.getElementById("statHigh").textContent = by["مرتفعة"] || 0;
    document.getElementById("statCritical").textContent = by["حرجة"] || 0;
  } catch (err) {
    console.error("فشل تحميل الإحصائيات:", err);
  }
}

/* ============ صندوق الوارد ============ */
async function loadHistory() {
  try {
    const res = await fetch(`${API_BASE}/history?limit=50`);
    const records = await res.json();
    const body = document.getElementById("historyBody");
    const empty = document.getElementById("emptyState");

    empty.hidden = records.length > 0;
    body.innerHTML = "";
    let maxId = lastSeenId;

    records.forEach(r => {
      const cls = levelToClass[r.risk_level] || "low";
      const tr = document.createElement("tr");
      tr.className = "level-" + cls;
      if (!firstLoad && r.id > lastSeenId) tr.classList.add("new-row");
      if (r.id > maxId) maxId = r.id;

      tr.innerHTML = `
        <td>${r.id}</td>
        <td class="sender-cell">${escapeHtml(r.sender || "-")}</td>
        <td class="subject-cell">${escapeHtml(r.subject || "(بدون عنوان)")}</td>
        <td>
          <span class="score-mini">
            <span class="track"><span class="fill" style="width:${r.risk_score}%;background:${levelColorVar[cls]}"></span></span>
            <span class="val">${r.risk_score}%</span>
          </span>
        </td>
        <td><span class="pill ${cls}">${r.risk_level}</span></td>
        <td>${new Date(r.created_at).toLocaleString("ar-EG-u-nu-latn")}</td>
      `;
      tr.addEventListener("click", () => openDetail(r.id));
      body.appendChild(tr);
    });

    lastSeenId = maxId;
    firstLoad = false;
  } catch (err) {
    console.error("فشل تحميل السجل:", err);
  }
}

/* ============ عرض الرسالة الكاملة ============ */
async function openDetail(recordId) {
  try {
    const res = await fetch(`${API_BASE}/history/${recordId}`);
    if (!res.ok) throw new Error("تعذر جلب التفاصيل");
    const r = await res.json();
    renderDetail({
      sender: r.sender,
      display_name: null,
      subject: r.subject,
      body: r.body,
      links: safeParseArray(r.links),
      attachments: safeParseArray(r.attachments),
      risk_score: r.risk_score,
      risk_level: r.risk_level,
      indicators: safeParseArray(r.triggered_indicators),
      recommendations: safeParseArray(r.recommendations),
      created_at: r.created_at,
    });
  } catch (err) {
    alert("خطأ في عرض الرسالة: " + err.message);
  }
}

function renderDetail(d) {
  const cls = levelToClass[d.risk_level] || "low";
  const dateStr = d.created_at ? new Date(d.created_at).toLocaleString("ar-EG-u-nu-latn") : "الآن";

  const linksHtml = d.links.length
    ? `<div class="chip-list">${d.links.map(l => {
        const short = l.length > 68 ? l.slice(0, 68) + "…" : l;
        return `<span class="chip link" title="${escapeHtml(l)}">🔗 ${escapeHtml(short)}</span>`;
      }).join("")}</div>`
    : `<p class="hint" style="margin:0">لا توجد روابط.</p>`;

  const attHtml = d.attachments.length
    ? `<div class="chip-list">${d.attachments.map(a => {
        const danger = /\.(exe|scr|bat|cmd|vbs|js|jar|msi|ps1|pif|hta|wsf)$/i.test(a) || (a.match(/\./g) || []).length >= 2;
        return `<span class="chip ${danger ? "danger" : ""}">${danger ? "⚠️ " : "📎 "}${escapeHtml(a)}</span>`;
      }).join("")}</div>`
    : `<p class="hint" style="margin:0">لا توجد مرفقات.</p>`;

  const indHtml = d.indicators.map(ind => `
    <div class="indicator ${ind.triggered ? "triggered" : "safe"}">
      <span class="icon">${ind.triggered ? "⚠️" : "✅"}</span>
      <div>
        <div class="i-title">${escapeHtml(ind.title)}</div>
        <div class="i-exp">${escapeHtml(ind.explanation)}</div>
        <div class="i-weight">الوزن: ${ind.weight}</div>
      </div>
    </div>
  `).join("");

  const recHtml = d.recommendations.length
    ? `<ul class="rec-list">${d.recommendations.map(x => `<li>${escapeHtml(x)}</li>`).join("")}</ul>`
    : "";

  const fromLine = d.display_name
    ? `<span class="v">${escapeHtml(d.display_name)} <span class="addr">&lt;${escapeHtml(d.sender)}&gt;</span></span>`
    : `<span class="v">${escapeHtml(d.sender || "-")}</span>`;

  document.getElementById("detailBody").innerHTML = `
    <div class="risk-hero ${cls}">
      <div class="score-ring">${d.risk_score}%</div>
      <div class="hero-text">
        <div class="level-name">مستوى الخطورة: ${escapeHtml(d.risk_level)}</div>
        <div class="track"><span class="fill" style="width:${d.risk_score}%;background:${levelColorVar[cls]}"></span></div>
      </div>
    </div>

    <div class="envelope">
      <div class="env-head">
        <div class="env-row"><span class="k">من:</span>${fromLine}</div>
        <div class="env-row"><span class="k">الموضوع:</span><span class="v">${escapeHtml(d.subject || "(بدون عنوان)")}</span></div>
        <div class="env-row"><span class="k">التاريخ:</span><span class="v">${dateStr}</span></div>
      </div>
      <div class="env-body">${escapeHtml(d.body || "(لا يوجد نص)")}</div>
    </div>

    <div class="detail-section">
      <h3>🔗 الروابط (${d.links.length})</h3>
      ${linksHtml}
    </div>

    <div class="detail-section">
      <h3>📎 المرفقات (${d.attachments.length})</h3>
      ${attHtml}
    </div>

    <div class="detail-section">
      <h3>🔍 المؤشرات المفحوصة</h3>
      ${indHtml}
    </div>

    ${recHtml ? `<div class="detail-section"><h3>💡 التوصيات التوعوية</h3>${recHtml}</div>` : ""}
  `;
  openModal("detailModal");
}

/* ============ ربط الأحداث ============ */
document.getElementById("refreshHistory").addEventListener("click", () => { loadHistory(); loadStats(); });

document.querySelectorAll(".modal-close").forEach(btn => {
  btn.addEventListener("click", () => closeModal(btn.dataset.close));
});
document.querySelectorAll(".modal-overlay").forEach(overlay => {
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.hidden = true; });
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") document.querySelectorAll(".modal-overlay").forEach(m => m.hidden = true);
});

/* ============ تحميل + تحديث حي ============ */
function refreshAll() { loadHistory(); loadStats(); }
refreshAll();
setInterval(refreshAll, 8000);
