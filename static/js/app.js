/* Concrete Defect AI — app.js */
(function () {
  "use strict";

  // ── Auth ─────────────────────────────────────────────────
  function getToken()  { return localStorage.getItem("cda_token"); }
  function getEmail()  { return localStorage.getItem("cda_email"); }
  function getTries()  { return parseInt(localStorage.getItem("cda_tries") || "0", 10); }

  function saveSession(token, email, tries) {
    localStorage.setItem("cda_token", token);
    localStorage.setItem("cda_email", email);
    localStorage.setItem("cda_tries", tries);
  }

  function clearSession() {
    localStorage.removeItem("cda_token");
    localStorage.removeItem("cda_email");
    localStorage.removeItem("cda_tries");
  }

  function updateUserBar(email, tries) {
    // Update nav auth area
    const guestBtns  = document.getElementById("nav-guest-btns");
    const userInfo   = document.getElementById("nav-user-info");
    const navEmail   = document.getElementById("nav-user-email");
    const navBadge   = document.getElementById("nav-tries-badge");
    if (guestBtns) guestBtns.style.display = "none";
    if (userInfo)  userInfo.style.display  = "flex";
    if (navEmail)  navEmail.textContent    = email;
    if (navBadge) {
      navBadge.textContent = tries + (tries === 1 ? " analysis" : " analyses") + " left";
      navBadge.className   = "tries-badge" + (tries === 0 ? " tries-empty" : tries === 1 ? " tries-warn" : "");
    }
    // Show analyzer form, hide gate
    const gate  = document.getElementById("analyzer-gate");
    const shell = document.getElementById("analyzer-shell");
    if (gate)  gate.style.display  = "none";
    if (shell) shell.style.display = "block";
  }

  function showGuestState() {
    const guestBtns  = document.getElementById("nav-guest-btns");
    const userInfo   = document.getElementById("nav-user-info");
    if (guestBtns) guestBtns.style.display = "flex";
    if (userInfo)  userInfo.style.display  = "none";
    // Show gate, hide analyzer form
    const gate  = document.getElementById("analyzer-gate");
    const shell = document.getElementById("analyzer-shell");
    if (gate)  gate.style.display  = "block";
    if (shell) shell.style.display = "none";
  }

  window.showAuthModal = function() {
    const overlay = document.getElementById("auth-overlay");
    if (overlay) overlay.style.display = "flex";
  };

  function hideAuthModal() {
    const overlay = document.getElementById("auth-overlay");
    if (overlay) overlay.style.display = "none";
  }

  window.switchTab = function(tab) {
    const isLogin = tab === "login";
    document.getElementById("tab-login").classList.toggle("active", isLogin);
    document.getElementById("tab-register").classList.toggle("active", !isLogin);
    document.getElementById("auth-submit").textContent = isLogin ? "Sign In" : "Create Account";
    document.getElementById("auth-footer-note").innerHTML = isLogin
      ? 'New here? <a href="#" onclick="switchTab(\'register\');return false;">Create a free account</a> — includes 3 free analyses.'
      : 'Already have an account? <a href="#" onclick="switchTab(\'login\');return false;">Sign in</a>';
    document.getElementById("auth-error").textContent = "";
    document.getElementById("auth-error").style.display = "none";
  };

  window.logout = function() {
    clearSession();
    showGuestState();
    showAuthModal();
  };

  // Auth form submit
  const authForm = document.getElementById("auth-form");
  if (authForm) {
    authForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const isLogin  = document.getElementById("tab-login").classList.contains("active");
      const email    = document.getElementById("auth-email").value.trim();
      const password = document.getElementById("auth-password").value;
      const errEl    = document.getElementById("auth-error");
      const btn      = document.getElementById("auth-submit");

      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span>' + (isLogin ? "Signing in…" : "Creating account…");
      errEl.style.display = "none";

      try {
        const res  = await fetch("/api/" + (isLogin ? "login" : "register"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Authentication failed.");
        saveSession(data.token, data.email, data.tries_remaining);
        updateUserBar(data.email, data.tries_remaining);
        hideAuthModal();
      } catch (err) {
        errEl.textContent   = err.message;
        errEl.style.display = "block";
      } finally {
        btn.disabled = false;
        btn.textContent = isLogin ? "Sign In" : "Create Account";
      }
    });
  }

  // On page load — check if already logged in
  (async function checkAuth() {
    const token = getToken();
    if (!token) { showGuestState(); return; }
    try {
      const res  = await fetch("/api/me", { headers: { Authorization: "Bearer " + token } });
      const data = await res.json();
      if (!res.ok) throw new Error();
      saveSession(token, data.email, data.tries_remaining);
      updateUserBar(data.email, data.tries_remaining);
    } catch {
      clearSession();
      showGuestState();
    }
  })();

  // ── DOM refs ─────────────────────────────────────────────
  const fileInput     = document.getElementById("photo-input");
  const dropzone      = document.getElementById("upload-dropzone");
  const form          = document.getElementById("analyzer-form");
  const progressWrap  = document.getElementById("progress-steps");
  const statusMsg     = document.getElementById("status-msg");
  const resultsArea   = document.getElementById("results-area");
  const imgPreviewBox = document.getElementById("img-preview");
  const annotBox      = document.getElementById("annot-image-box");
  const annotCard     = document.getElementById("annot-card");
  const annotBadge    = document.getElementById("annot-badge");
  const distressTable = document.getElementById("distress-table");
  const reportContent = document.getElementById("report-content");
  const dlBtn         = document.getElementById("download-pdf-btn");
  const submitBtn     = document.getElementById("submit-btn");

  // ── State ────────────────────────────────────────────────
  let currentFile     = null;
  let originalB64     = "";
  let annotatedB64    = "";
  let reportText      = "";

  // ── Progress steps ──────────────────────────────────────
  const STEPS = ["step-analyze", "step-annotate", "step-done"];
  function setStep(active) {
    progressWrap.classList.add("show");
    STEPS.forEach((id, i) => {
      const node = document.getElementById(id);
      if (!node) return;
      node.classList.remove("active", "done");
      const idx = STEPS.indexOf(active);
      if (i < idx)  node.classList.add("done");
      if (id === active) node.classList.add("active");
    });
  }
  function clearProgress() {
    progressWrap.classList.remove("show");
    STEPS.forEach(id => {
      const n = document.getElementById(id);
      if (n) n.classList.remove("active", "done");
    });
  }

  // ── Status messages ──────────────────────────────────────
  function setStatus(msg, type) {
    statusMsg.className = "status-msg show " + (type || "");
    statusMsg.innerHTML = (type === "loading" ? '<span class="spinner"></span>' : "") + msg;
  }
  function clearStatus() {
    statusMsg.className = "status-msg";
    statusMsg.textContent = "";
  }

  // ── File handling ────────────────────────────────────────
  function handleFile(file) {
    if (!file || !file.type.startsWith("image/")) {
      setStatus("Please select a valid image file (JPEG, PNG, WebP).", "error");
      return;
    }

    currentFile = file;
    dropzone.classList.add("has-file");
    dropzone.querySelector(".upload-dropzone-label").textContent = file.name;
    dropzone.querySelector(".upload-dropzone-hint").textContent =
      (file.size / 1024 / 1024).toFixed(1) + " MB";

    const reader = new FileReader();
    reader.onload = (e) => { originalB64 = e.target.result; };
    reader.readAsDataURL(file);

    clearStatus();
  }

  dropzone.addEventListener("click", (e) => {
    e.preventDefault();
    fileInput.click();
  });
  fileInput.addEventListener("change", () => {
    if (fileInput.files && fileInput.files[0]) handleFile(fileInput.files[0]);
  });
  ["dragenter", "dragover"].forEach(evt =>
    dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.add("drag-over"); })
  );
  ["dragleave", "dragend", "drop"].forEach(evt =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove("drag-over");
      if (evt === "drop" && e.dataTransfer && e.dataTransfer.files[0]) {
        try {
          const dt = new DataTransfer();
          dt.items.add(e.dataTransfer.files[0]);
          fileInput.files = dt.files;
        } catch (_) {}
        handleFile(e.dataTransfer.files[0]);
      }
    })
  );

  // ── Report formatter ─────────────────────────────────────
  function inlineFmt(s) {
    return s
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g,     "<em>$1</em>")
      .replace(/`(.*?)`/g,       "<code>$1</code>");
  }

  function formatReport(text) {
    const lines   = text.split("\n");
    let html      = "";
    let inUl      = false;
    let inOl      = false;
    let inTable   = false;
    let tableRows = [];
    let paraLines = [];

    function flushPara() {
      if (!paraLines.length) return;
      const content = paraLines.join(" ").trim();
      if (content) html += "<p>" + content + "</p>\n";
      paraLines = [];
    }
    function flushUl()  { if (inUl)  { html += "</ul>\n";  inUl  = false; } }
    function flushOl()  { if (inOl)  { html += "</ol>\n";  inOl  = false; } }
    function flushList(){ flushUl(); flushOl(); }
    function flushTable() {
      if (!tableRows.length) { inTable = false; return; }
      html += '<div class="report-table-wrap"><table class="report-table">';
      tableRows.forEach((cells, i) => {
        if (i === 1 && cells.every(c => /^[-: ]+$/.test(c))) return; // skip separator row
        const tag = i === 0 ? "th" : "td";
        html += "<tr>" + cells.map(c => `<${tag}>${inlineFmt(c.trim())}</${tag}>`).join("") + "</tr>";
      });
      html += "</table></div>\n";
      tableRows = [];
      inTable   = false;
    }

    for (const raw of lines) {
      const line = raw;
      const trim = line.trim();

      // ── Markdown table row
      if (trim.startsWith("|") && trim.endsWith("|")) {
        flushPara(); flushList();
        inTable = true;
        tableRows.push(trim.split("|").slice(1, -1));
        continue;
      }
      if (inTable) flushTable();

      // ── Headings
      const h2 = trim.match(/^##\s+(.+)/);
      const h3 = trim.match(/^###\s+(.+)/);
      const h4 = trim.match(/^####\s+(.+)/);
      if (h4) { flushPara(); flushList(); html += "<h4>" + inlineFmt(h4[1]) + "</h4>\n"; continue; }
      if (h3) { flushPara(); flushList(); html += "<h3>" + inlineFmt(h3[1]) + "</h3>\n"; continue; }
      if (h2) { flushPara(); flushList(); html += "<h2>" + inlineFmt(h2[1]) + "</h2>\n"; continue; }

      // ── Horizontal rule
      if (/^---+$/.test(trim)) { flushPara(); flushList(); html += '<hr class="report-hr">\n'; continue; }

      // ── Bullet list
      const bullet = trim.match(/^[-*→►•]\s+(.+)/);
      if (bullet) {
        flushPara();
        if (!inUl) { flushOl(); html += "<ul>\n"; inUl = true; }
        html += "<li>" + inlineFmt(bullet[1]) + "</li>\n";
        continue;
      }

      // ── Numbered list
      const numbered = trim.match(/^\d+[.)]\s+(.+)/);
      if (numbered) {
        flushPara();
        if (!inOl) { flushUl(); html += "<ol>\n"; inOl = true; }
        html += "<li>" + inlineFmt(numbered[1]) + "</li>\n";
        continue;
      }

      // ── Blank line = paragraph break
      if (trim === "") { flushPara(); flushList(); continue; }

      // ── Regular text
      flushList();
      paraLines.push(inlineFmt(trim));
    }

    flushPara(); flushList(); flushTable();
    return '<div class="report-content">' + html + "</div>";
  }

  // ── PDF download ─────────────────────────────────────────
  async function downloadPdf() {
    dlBtn.disabled = true;
    dlBtn.innerHTML = '<span class="spinner"></span>Building PDF…';
    try {
      const res = await fetch("/api/export-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          report:        reportText,
          original_b64:  originalB64,
          annotated_b64: annotatedB64,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(err.detail || "PDF generation failed");
      }
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href = url;
      a.download = "concrete-defect-report.pdf";
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert("PDF export failed: " + err.message);
    } finally {
      dlBtn.disabled = false;
      dlBtn.innerHTML = "⬇ Download PDF";
    }
  }
  dlBtn.addEventListener("click", downloadPdf);

  // ── Show / reset results ─────────────────────────────────
  function showOriginalImage() {
    if (!currentFile) return;
    resultsArea.classList.add("show");
    imgPreviewBox.innerHTML = "";
    const img = document.createElement("img");
    img.src = URL.createObjectURL(currentFile);
    img.alt = "Uploaded concrete image";
    imgPreviewBox.appendChild(img);
  }

  function showAnnotatedImage(b64, count, summary) {
    annotatedB64 = b64;
    annotCard.style.display = "block";
    annotBadge.textContent = count + " crack" + (count !== 1 ? "s" : "") + " mapped";

    annotBox.innerHTML = "";
    const img = document.createElement("img");
    img.src = b64;
    img.alt = "AI defect map";
    img.style.cssText = "width:100%;height:auto;display:block;border-radius:8px;";
    annotBox.appendChild(img);

    if (summary && (summary.primary_distress || summary.overall_severity)) {
      distressTable.innerHTML = "";
      distressTable.style.display = "block";
      const rows = [
        ["Primary distress",   summary.primary_distress,   false],
        ["Secondary distress", summary.secondary_distress, false],
        ["Overall severity",   summary.overall_severity,   true],
      ];
      rows.forEach(([key, val, isWarn]) => {
        if (!val) return;
        const row = document.createElement("div");
        row.className = "distress-row";
        row.innerHTML =
          `<span class="distress-key">${key}</span>` +
          `<span class="distress-val${isWarn ? " distress-sev" : ""}">${val}</span>`;
        distressTable.appendChild(row);
      });
    }
  }

  function resetResults() {
    resultsArea.classList.remove("show");
    annotCard.style.display = "none";
    distressTable.style.display = "none";
    distressTable.innerHTML = "";
    annotBox.innerHTML = "";
    imgPreviewBox.innerHTML = "";
    reportContent.innerHTML = "";
    annotatedB64 = "";
    reportText   = "";
    dlBtn.disabled = true;
    dlBtn.textContent = "⬇ Download PDF";
  }

  // ── Main form submit ─────────────────────────────────────
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearStatus();
    resetResults();
    clearProgress();

    if (!currentFile) {
      setStatus("Please upload an image before generating a report.", "error");
      return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner"></span>Analysing…';
    showOriginalImage();

    // ── Step 1: Text report ───────────────────────────────
    setStep("step-analyze");
    setStatus("Generating engineering report (this may take 30–60 seconds)…", "loading");

    const fd = new FormData();
    fd.append("image", currentFile);
    ["element_type", "structure_age", "exposure", "water_infiltration", "crack_evolution", "previous_repair", "customer_notes"]
      .forEach(name => {
        const el = form.querySelector(`[name="${name}"]`);
        fd.append(name, el ? el.value : "");
      });

    try {
      const token = getToken();
      const r1 = await fetch("/api/analyze", {
        method: "POST",
        headers: token ? { "Authorization": "Bearer " + token } : {},
        body: fd,
      });
      const d1 = await r1.json();
      if (!r1.ok) throw new Error(d1.detail || "Analysis failed.");

      reportText = d1.report;
      reportContent.innerHTML = formatReport(reportText);
      resultsArea.classList.add("show");

      // Update tries display
      if (d1.tries_remaining !== undefined) {
        const email = getEmail();
        saveSession(token, email, d1.tries_remaining);
        updateUserBar(email, d1.tries_remaining);
      }

      // scroll to results
      setTimeout(() => resultsArea.scrollIntoView({ behavior: "smooth", block: "start" }), 80);

      dlBtn.disabled = false;

      // ── Step 2: Annotations ─────────────────────────────
      setStep("step-annotate");
      setStatus("Mapping defects on image…", "loading");

      const fd2 = new FormData();
      fd2.append("image", currentFile);

      const r2 = await fetch("/api/annotate", {
        method: "POST",
        headers: token ? { "Authorization": "Bearer " + token } : {},
        body: fd2,
      });
      const d2 = await r2.json();

      if (r2.ok && d2.annotated_b64) {
        showAnnotatedImage(d2.annotated_b64, d2.count || 0, d2.distress_summary || {});
        setStep("step-done");
        setStatus("Analysis complete. Your report and defect map are ready.", "success");
      } else {
        setStep("step-done");
        setStatus("Report ready. Defect map unavailable: " + (d2.detail || "No annotations returned."), "success");
      }
    } catch (err) {
      clearProgress();
      setStatus("Error: " + err.message, "error");
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = "Generate AI Report";
    }
  });
})();
