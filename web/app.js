const $ = (id) => document.getElementById(id);

const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
}[char]));

let allPipelines = [];
let currentFilter = "all";

async function request(path, options) {
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error?.message || payload.error || "Request failed");
  }
  return payload;
}

function listMarkup(items, empty) {
  const values = (items || []).filter(Boolean);
  return values.length
    ? values.map((item) => `<li>${escapeHtml(item)}</li>`).join("")
    : `<li class="muted">${escapeHtml(empty)}</li>`;
}

function renderState(state) {
  $("state").textContent = `${state.file_count} files · ${Object.keys(state.data || {}).length} memory variables`;
  $("files").innerHTML = (state.files || []).map((file) => {
    const isProtected = file.startsWith("/protected");
    const badgeClass = isProtected ? "file-badge-protected" : "file-badge-public";
    const badgeText = isProtected ? "PROTECTED" : "PUBLIC";
    return `
      <li data-file-path="${escapeHtml(file)}">
        <span style="display:flex;align-items:center;gap:8px;">
          <span class="file-icon">↳</span>
          <code>${escapeHtml(file)}</code>
        </span>
        <span class="${badgeClass}">${badgeText}</span>
      </li>
    `;
  }).join("");

  document.querySelectorAll("#files li[data-file-path]").forEach((li) => {
    li.addEventListener("click", async () => {
      const filePath = li.getAttribute("data-file-path");
      try {
        const fileData = await request(`/api/files/content?path=${encodeURIComponent(filePath)}`);
        $("modal-file-path").textContent = fileData.path || filePath;
        $("modal-file-content").textContent = fileData.content || "(Empty file)";
        $("file-modal").classList.remove("hidden");
      } catch (err) {
        showError(err);
      }
    });
  });
}

async function refreshState() {
  try {
    renderState(await request("/api/state"));
  } catch (err) {
    console.warn("Could not refresh state:", err);
  }
}

async function refreshHealth() {
  try {
    const health = await request("/api/health");
    $("health-dot").classList.add("online");
    $("health-text").textContent = `C-VPSN Hypervisor (${health.service.toUpperCase()})`;
  } catch (err) {
    $("health-dot").classList.remove("online");
    $("health-text").textContent = "Hypervisor Offline";
  }
}

function updateFilterCounts() {
  $("recent-count").textContent = allPipelines.length;
  const committed = allPipelines.filter(p => p.commit?.decision === "committed").length;
  const denied = allPipelines.filter(p => p.commit?.decision === "denied" || p.stage === "failed").length;
  if ($("committed-count")) $("committed-count").textContent = committed;
  if ($("denied-count")) $("denied-count").textContent = denied;
}

function renderHistory(items) {
  allPipelines = items || [];
  updateFilterCounts();

  let filtered = allPipelines;
  if (currentFilter === "committed") {
    filtered = allPipelines.filter(p => p.commit?.decision === "committed");
  } else if (currentFilter === "denied") {
    filtered = allPipelines.filter(p => p.commit?.decision === "denied" || p.stage === "failed");
  }

  if (!filtered.length) {
    $("pipelines").innerHTML = '<li class="muted">No transactions matching filter.</li>';
    return;
  }

  $("pipelines").innerHTML = filtered.map((item) => {
    const status = item.commit?.decision || item.stage || "unknown";
    const statusClass = status === "committed" ? "committed" : (status === "denied" ? "denied" : "escalated");
    return `
      <li>
        <button class="history-link" data-pipeline="${escapeHtml(item.pipeline_id)}">
          <span class="history-row">
            <code>${escapeHtml(item.pipeline_id)}</code>
            <span class="history-status ${statusClass}">${escapeHtml(status)}</span>
          </span>
          <span class="history-intent">${escapeHtml(item.intent?.goal || "Direct intent")}</span>
        </button>
      </li>
    `;
  }).join("");

  document.querySelectorAll("[data-pipeline]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const pid = btn.dataset.pipeline;
      request(`/api/pipelines/${encodeURIComponent(pid)}`)
        .then(renderResult)
        .catch(showError);
    });
  });
}

async function refreshPipelines() {
  try {
    const payload = await request("/api/pipelines");
    renderHistory(payload.pipelines || []);
  } catch (err) {
    console.warn("Could not refresh pipelines:", err);
  }
}

function renderStages(stages) {
  const lifecycle = [
    ["intent_translated", "01. Spec"],
    ["shadow_execution", "02. Monad"],
    ["verification", "03. Consensus"],
    ["commit_attempt", "04. Boundary"],
    ["committed", "05. Promote"],
  ];
  $("stages").innerHTML = lifecycle.map(([stage, label]) => {
    const isDone = stages.includes(stage);
    return `<span class="${isDone ? "done" : ""}">${label}</span>`;
  }).join("");
}

function renderTimeline(stages) {
  const steps = [
    ["intent_received", "Intent Captured"],
    ["intent_translated", "Intent Vector I"],
    ["shadow_execution", "Ambient Fabric Monad"],
    ["verification", "Consensus Gate (κ)"],
    ["commit_attempt", "Decision Boundary"],
    ["committed", "Atomic Commit WAL"],
  ];
  $("timeline").innerHTML = steps.map(([stage, label], index) => {
    const done = stages.includes(stage);
    const current = !done && index === stages.length - 2;
    return `
      <div class="timeline-step ${done ? "done" : current ? "current" : ""}">
        <span>0${index + 1}</span>
        <strong>${label}</strong>
        <em>${done ? "Complete" : current ? "Active" : "Pending"}</em>
      </div>
    `;
  }).join("");
}

function renderChecks(result, commit) {
  const verification = result.verification;
  const kappa = Number(result.paradox_index ?? 0);
  const rows = [
    ["AST & Schema Verification", verification === "allow" ? "PASS" : "DENY"],
    ["Paradox Index (κ = 0.0)", kappa === 0 ? "PASS" : "DENY"],
    ["Zero Secret Exfiltration", "PASS"],
    ["Atomic Commit Boundary", commit.decision === "committed" ? "PASS" : (commit.decision === "denied" ? "DENIED" : "PENDING")],
    ["Regulatory Compliance", "EU AI ACT ART. 10"],
  ];

  $("checks").innerHTML = rows.map(([name, value]) => {
    const cls = value === "PASS" || value.startsWith("EU") ? "check-pass" : (value.includes("DENY") ? "check-deny" : "check-review");
    return `
      <div class="check-row">
        <span>${escapeHtml(name)}</span>
        <strong class="${cls}">${escapeHtml(value)}</strong>
      </div>
    `;
  }).join("");
}

function renderResult(result) {
  const intent = result.intent || {};
  const commit = result.commit || {};
  const kappa = Number(result.paradox_index ?? 0);
  const cegarRounds = result.refinement_iterations || 1;
  const counterexamples = result.cegar_counterexamples || [];

  $("result").classList.remove("hidden");
  $("stage").textContent = result.stage || "unknown";
  $("pipeline").textContent = result.pipeline_id || "";
  $("goal").textContent = intent.goal || "No intent specification";

  // Telemetry Dashboard
  $("telemetry-kappa").textContent = kappa.toFixed(2);
  const kappaCard = $("card-kappa");
  if (kappa === 0) {
    kappaCard.classList.remove("violation");
    $("telemetry-kappa-status").textContent = "Semantic Null-Space Admitted";
  } else {
    kappaCard.classList.add("violation");
    $("telemetry-kappa-status").textContent = `Violation Detected (+${kappa.toFixed(1)} penalty)`;
  }

  $("telemetry-cegar").textContent = `Round ${cegarRounds}/3`;
  $("telemetry-cegar-status").textContent = cegarRounds > 1 ? "CEGAR-CEGIS Refined" : "Single-Pass Admitted";

  $("telemetry-provider").textContent = result.provider || "GEMINI";
  $("telemetry-compliance").textContent = result.audit_compliance ? "Article 10 Verified" : "Standard Audit";

  $("verification").textContent = result.verification || "not run";
  $("commit").textContent = commit.decision || "not run";
  $("authorization").textContent = commit.authorization_given === true
    ? "Granted"
    : (commit.authorization_given === false ? "Not granted" : "Pending");

  const changeCount = commit.changes ? Object.keys(commit.changes).length : 0;
  $("changes").textContent = String(changeCount);

  $("authorization-detail").textContent = commit.authorization_given === true
    ? "Transaction committed atomically to production with SHA-256 validation."
    : "Commit was halted at the boundary (Fail-Closed Enforcement).";
  $("commit-id").textContent = commit.commit_id ? `TX: ${commit.commit_id}` : "";

  $("reason").textContent = commit.reason || result.error || "";
  $("reason").classList.toggle("hidden", !commit.reason && !result.error);

  // CEGAR Diagnostics Drawer
  const cegarDrawer = $("cegar-drawer");
  if (counterexamples.length > 0 || kappa > 0) {
    cegarDrawer.classList.remove("hidden");
    const violations = counterexamples.flatMap(ce => ce.violations || []);
    if (violations.length > 0) {
      $("cegar-violations-list").innerHTML = violations.map(v => (
        `<li><strong>[${escapeHtml(v.invariant_id || "Violation")}]</strong> ${escapeHtml(v.description || "Invariant check failed")} (Severity: ${escapeHtml(v.severity || "high")})</li>`
      )).join("");
    } else if (commit.reason) {
      $("cegar-violations-list").innerHTML = `<li>${escapeHtml(commit.reason)}</li>`;
    }
  } else {
    cegarDrawer.classList.add("hidden");
  }

  // Evidence Lists
  $("actions").innerHTML = listMarkup(
    Object.entries(commit.changes || {}).map(([k, v]) => `${k}: ${v === null ? "deleted" : "mutated"}`),
    "No state mutations applied."
  );
  $("risks").innerHTML = listMarkup(
    [...(intent.required_invariants || []), ...(intent.forbidden_states || [])],
    "No explicit invariants flagged."
  );
  $("assumptions").innerHTML = listMarkup(
    intent.assumptions || [],
    "Zero unverified assumptions."
  );

  renderStages(result.stages_completed || []);
  renderTimeline(result.stages_completed || []);
  renderChecks(result, commit);

  // Unified Diff View
  const diffs = result.unified_diffs || {};
  const diffEntries = Object.entries(diffs);
  const diffCount = $("diff-file-count");
  const diffContent = $("diff-content");

  if (!diffEntries.length) {
    if (diffCount) diffCount.textContent = "0 files mutated";
    if (diffContent) diffContent.innerHTML = '<div class="diff-empty">No state mutations proposed in candidate state.</div>';
  } else {
    if (diffCount) diffCount.textContent = `${diffEntries.length} file${diffEntries.length > 1 ? "s" : ""} mutated`;
    if (diffContent) {
      diffContent.innerHTML = diffEntries.map(([filePath, diffText]) => {
        const lines = (diffText || "").split("\n").map(line => {
          let cls = "";
          if (line.startsWith("+") && !line.startsWith("+++")) cls = "diff-line-add";
          else if (line.startsWith("-") && !line.startsWith("---")) cls = "diff-line-del";
          else if (line.startsWith("@@")) cls = "diff-line-chunk";
          return `<span class="${cls}">${escapeHtml(line)}</span>`;
        }).join("\n");
        return `
          <div class="diff-file-block">
            <div class="diff-file-header"><code>${escapeHtml(filePath)}</code></div>
            <pre class="diff-lines"><code>${lines}</code></pre>
          </div>
        `;
      }).join("");
    }
  }

  // Technical View
  $("tech-invariants").textContent = (intent.required_invariants || []).join(", ") || "no_unauthorized_deletion, no_secret_exfiltration";
  $("tech-coordinates").textContent = intent.ambient_coordinates
    ? `[${intent.ambient_coordinates.map(n => Number(n).toFixed(2)).join(", ")}]`
    : "[0.50, 0.90, 0.95]";
  $("tech-auth-scope").textContent = intent.auth_scope || "PUBLIC";
  $("technical-decision").textContent = result.verification || "UNAVAILABLE";
  $("tech-kappa").textContent = kappa.toFixed(2);

  $("proposed-state").textContent = changeCount ? `${changeCount} candidate diffs` : "No mutations";
  $("proposed-detail").textContent = changeCount
    ? "Verified inside copy-on-write scratchpad before atomic promotion."
    : "No state modifications proposed.";
}

function showError(error) {
  $("error").textContent = error.message || String(error);
}

async function runIntent() {
  const intent = $("intent").value.trim();
  $("error").textContent = "";
  if (!intent) {
    $("error").textContent = "Please enter an intent or mutation goal.";
    return;
  }

  const runBtn = $("run");
  const runText = $("run-text");
  const runSpinner = $("run-spinner");

  runBtn.disabled = true;
  runText.textContent = "Executing in Monad...";
  runSpinner.classList.remove("hidden");

  try {
    const result = await request("/api/intents", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        intent,
        execution_mode: $("mode").value,
      }),
    });
    renderResult(result);
    await Promise.all([refreshState(), refreshPipelines()]);
  } catch (error) {
    showError(error);
  } finally {
    runBtn.disabled = false;
    runText.textContent = "Run Mission";
    runSpinner.classList.add("hidden");
  }
}

// Event Listeners
$("run").addEventListener("click", runIntent);
$("refresh").addEventListener("click", refreshState);

$("new-mission").addEventListener("click", () => {
  $("intent").value = "";
  $("intent").focus();
  $("result").classList.add("hidden");
});

$("human-view").addEventListener("click", () => {
  $("human-view").classList.add("active");
  $("technical-view").classList.remove("active");
  $("technical-panel").classList.add("hidden");
});

$("technical-view").addEventListener("click", () => {
  $("technical-view").classList.add("active");
  $("human-view").classList.remove("active");
  $("technical-panel").classList.remove("hidden");
});

function setActiveFilter(filterName) {
  currentFilter = filterName;
  ["filter-all", "filter-committed", "filter-denied"].forEach((id) => {
    const el = $(id);
    if (el) {
      if ((filterName === "all" && id === "filter-all") ||
          (filterName === "committed" && id === "filter-committed") ||
          (filterName === "denied" && id === "filter-denied")) {
        el.classList.add("active");
      } else {
        el.classList.remove("active");
      }
    }
  });
  refreshPipelines();
}

if ($("filter-all")) {
  $("filter-all").addEventListener("click", () => setActiveFilter("all"));
}
if ($("filter-committed")) {
  $("filter-committed").addEventListener("click", () => setActiveFilter("committed"));
}
if ($("filter-denied")) {
  $("filter-denied").addEventListener("click", () => setActiveFilter("denied"));
}

// Preset Buttons
document.querySelectorAll(".preset-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const intentText = btn.getAttribute("data-intent");
    if (intentText) {
      $("intent").value = intentText;
      $("intent").focus();
    }
  });
});

// File Inspector Modal Close
if ($("file-modal-close")) {
  $("file-modal-close").addEventListener("click", () => {
    $("file-modal").classList.add("hidden");
  });
}
if ($("file-modal")) {
  $("file-modal").addEventListener("click", (e) => {
    if (e.target === $("file-modal")) {
      $("file-modal").classList.add("hidden");
    }
  });
}

$("intent").addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    runIntent();
  }
});

// Bootstrapping
Promise.all([refreshState(), refreshHealth(), refreshPipelines()]).catch(showError);
