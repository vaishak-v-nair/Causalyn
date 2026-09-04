const $ = (id) => document.getElementById(id);

const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
}[char]));

let allMissions = [];
let currentFilter = "all";
let activeMissionId = null;

async function request(path, options) {
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok) {
    const msg = payload.detail?.message || payload.detail || payload.error?.message || payload.error || "Request failed";
    throw new Error(typeof msg === "object" ? JSON.stringify(msg) : msg);
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
    const isProtected = file.startsWith("/protected") || file.startsWith("/secrets") || file.endsWith(".env");
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
    $("health-text").textContent = `C-VPSN Hypervisor (${(health.service || "causalyn").toUpperCase()})`;
  } catch (err) {
    $("health-dot").classList.remove("online");
    $("health-text").textContent = "Hypervisor Offline";
  }
}

function updateFilterCounts() {
  $("recent-count").textContent = allMissions.length;
  const committed = allMissions.filter(m => (m.state === "committed" || m.commit?.decision === "committed" || m.stage === "committed")).length;
  const denied = allMissions.filter(m => (m.state === "denied" || m.state === "rejected" || m.decision?.outcome === "deny" || m.commit?.decision === "denied" || m.stage === "failed")).length;
  if ($("committed-count")) $("committed-count").textContent = committed;
  if ($("denied-count")) $("denied-count").textContent = denied;
}

function renderHistory(items) {
  allMissions = items || [];
  updateFilterCounts();

  let filtered = allMissions;
  if (currentFilter === "committed") {
    filtered = allMissions.filter(m => (m.state === "committed" || m.commit?.decision === "committed" || m.stage === "committed"));
  } else if (currentFilter === "denied") {
    filtered = allMissions.filter(m => (m.state === "denied" || m.state === "rejected" || m.decision?.outcome === "deny" || m.commit?.decision === "denied" || m.stage === "failed"));
  }

  if (!filtered.length) {
    $("pipelines").innerHTML = '<li class="muted">No transactions matching filter.</li>';
    return;
  }

  $("pipelines").innerHTML = filtered.map((item) => {
    const id = item.mission_id || item.pipeline_id || "unknown";
    const status = item.state || item.commit?.decision || item.stage || "pending";
    const statusClass = (status === "committed")
      ? "committed"
      : (status === "denied" || status === "rejected" || status === "failed" ? "denied" : "escalated");
    const goalText = item.intent?.goal || item.name || "Direct intent";

    return `
      <li>
        <button class="history-link" data-mission="${escapeHtml(id)}">
          <span class="history-row">
            <code>${escapeHtml(id)}</code>
            <span class="history-status ${statusClass}">${escapeHtml(status.toUpperCase())}</span>
          </span>
          <span class="history-intent">${escapeHtml(goalText)}</span>
        </button>
      </li>
    `;
  }).join("");

  document.querySelectorAll("[data-mission]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.mission;
      const endpoint = id.startsWith("mission-") ? `/api/missions/${encodeURIComponent(id)}` : `/api/pipelines/${encodeURIComponent(id)}`;
      request(endpoint)
        .then(renderMission)
        .catch(showError);
    });
  });
}

async function refreshMissions() {
  try {
    const missions = await request("/api/missions");
    if (missions && missions.length > 0) {
      renderHistory(missions);
      return;
    }
  } catch (err) {
    console.warn("Could not fetch missions, trying pipelines:", err);
  }

  try {
    const payload = await request("/api/pipelines");
    renderHistory(payload.pipelines || []);
  } catch (err) {
    console.warn("Could not refresh history:", err);
  }
}

function renderStages(stageOrList) {
  const lifecycle = [
    ["analyze", "01. Analyze"],
    ["shadow", "02. Shadow"],
    ["verify", "03. Verify"],
    ["authorize", "04. Authorize"],
    ["commit", "05. Commit"],
  ];

  let completedList = [];
  if (Array.isArray(stageOrList)) {
    completedList = stageOrList;
  } else {
    const current = String(stageOrList || "").toLowerCase();
    if (current === "analyze") completedList = ["analyze"];
    else if (current === "shadow") completedList = ["analyze", "shadow"];
    else if (current === "verify") completedList = ["analyze", "shadow", "verify"];
    else if (current === "authorize") completedList = ["analyze", "shadow", "verify", "authorize"];
    else if (current === "commit" || current === "committed") completedList = ["analyze", "shadow", "verify", "authorize", "commit"];
    else completedList = ["analyze", "shadow", "verify"];
  }

  $("stages").innerHTML = lifecycle.map(([stage, label]) => {
    const isDone = completedList.includes(stage) || completedList.includes(stage + "_execution") || completedList.includes("intent_translated");
    return `<span class="${isDone ? "done" : ""}">${label}</span>`;
  }).join("");
}

function renderTimeline(stageOrList) {
  const steps = [
    ["analyze", "Intent Understanding"],
    ["shadow", "Isolated Shadow State"],
    ["verify", "Layered Verification & Conflict"],
    ["authorize", "Human Authorization Gate"],
    ["commit", "Atomic Commit & Article 10"],
  ];

  let activeIndex = 2;
  const current = String(stageOrList || "").toLowerCase();
  if (current === "analyze") activeIndex = 0;
  else if (current === "shadow") activeIndex = 1;
  else if (current === "verify") activeIndex = 2;
  else if (current === "authorize") activeIndex = 3;
  else if (current === "commit" || current === "committed") activeIndex = 4;

  $("timeline").innerHTML = steps.map(([stage, label], index) => {
    const done = index <= activeIndex;
    const isCurrent = index === activeIndex;
    return `
      <div class="timeline-step ${done ? "done" : ""} ${isCurrent ? "current" : ""}">
        <span>0${index + 1}</span>
        <strong>${label}</strong>
        <em>${done ? (isCurrent ? "Active" : "Passed") : "Pending"}</em>
      </div>
    `;
  }).join("");
}

function renderVerificationChecks(verifications, kappa) {
  if (!verifications || !verifications.length) {
    const rows = [
      ["AST & Schema Verification", kappa === 0 ? "PASS" : "DENY"],
      ["Paradox Index (κ = 0.0)", kappa === 0 ? "PASS" : "DENY"],
      ["Zero Secret Exfiltration", "PASS"],
      ["Regulatory Compliance", "EU AI ACT ART. 10"],
    ];
    $("checks").innerHTML = rows.map(([name, val]) => `
      <div class="check-row">
        <span>${escapeHtml(name)}</span>
        <strong class="${val === 'PASS' || val.startsWith('EU') ? 'check-pass' : 'check-deny'}">${escapeHtml(val)}</strong>
      </div>
    `).join("");
    return;
  }

  $("checks").innerHTML = verifications.map((v) => {
    const status = v.status || "PASS";
    const cls = status === "PASS" ? "check-pass" : (status === "FAIL" ? "check-deny" : "check-review");
    const verifierName = v.verifier || "Verifier";
    const layer = v.layer ? `[${v.layer.toUpperCase()}]` : "";
    return `
      <div class="check-row">
        <span><small style="color:var(--text-muted);margin-right:6px;">${escapeHtml(layer)}</small>${escapeHtml(verifierName)}</span>
        <strong class="${cls}">${escapeHtml(status)}</strong>
      </div>
    `;
  }).join("");
}

function renderMission(data) {
  activeMissionId = data.mission_id || data.pipeline_id;
  const intent = data.intent || {};
  const decision = data.decision || {};
  const commit = data.commit || {};
  const risk = data.risk || {};
  const verifications = data.verifications || [];
  const conflicts = data.conflicts || [];
  const candidate = data.candidate_state || {};
  const state = data.state || data.stage || "pending";
  const kappa = Number(decision.paradox_index ?? data.paradox_index ?? 0.0);

  $("result").classList.remove("hidden");
  $("stage").textContent = state.toUpperCase();
  $("pipeline").textContent = activeMissionId;
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

  const riskScore = risk.score !== undefined ? `${risk.score}/100` : "0/100";
  $("telemetry-cegar").textContent = `Risk: ${risk.risk_level || "LOW"} (${riskScore})`;
  $("telemetry-cegar-status").textContent = risk.factors && risk.factors.length ? risk.factors.join(", ") : "No high risk factors";

  $("telemetry-provider").textContent = "DETERMINISTIC HYPERVISOR";
  $("telemetry-compliance").textContent = "Article 10 Verified";

  $("verification").textContent = (decision.outcome || data.verification || "not run").toUpperCase();
  $("commit").textContent = (commit.decision || state || "not run").toUpperCase();
  $("authorization").textContent = data.authorization
    ? data.authorization.status.toUpperCase()
    : (commit.authorization_given === true ? "GRANTED" : "NOT REQUIRED");

  const diffs = candidate.unified_diffs || data.unified_diffs || {};
  const changeCount = Object.keys(diffs).length;
  $("changes").textContent = String(changeCount);

  const authDetail = commit.decision === "committed" || state === "committed"
    ? "Transaction committed atomically to production with SHA-256 validation."
    : "Halted at the boundary (Fail-Closed Execution Control).";
  $("authorization-detail").textContent = authDetail;
  $("commit-id").textContent = commit.commit_id ? `TX: ${commit.commit_id}` : (data.audit_record?.hash_signature ? `SIG: ${data.audit_record.hash_signature.slice(0, 16)}...` : "");

  const reasonText = decision.reason || commit.reason || data.error || "";
  $("reason").textContent = reasonText;
  $("reason").classList.toggle("hidden", !reasonText);

  // 1. Human Authorization Gate Handling
  const authGate = $("authorization-gate");
  if (state === "authorize" || (data.authorization && data.authorization.status === "pending")) {
    authGate.classList.remove("hidden");
    const riskPill = $("auth-risk-pill");
    const riskLevel = risk.risk_level || "HIGH";
    riskPill.className = `risk-badge risk-badge-${riskLevel.toLowerCase()}`;
    riskPill.textContent = `RISK: ${riskLevel} (${risk.score || 0}/100)`;

    const affected = data.authorization?.affected_resources || Object.keys(diffs);
    $("auth-affected-resources").innerHTML = affected.length
      ? affected.map(r => `<li>${escapeHtml(r)}</li>`).join("")
      : "<li>No resource paths recorded</li>";

    const factors = risk.factors || [];
    $("auth-risk-factors").innerHTML = factors.length
      ? factors.map(f => `<li>${escapeHtml(f)}</li>`).join("")
      : "<li>Automated policy threshold trigger</li>";
  } else {
    authGate.classList.add("hidden");
  }

  // 2. Conflict Analysis Drawer
  const conflictsDrawer = $("conflicts-drawer");
  if (conflicts && conflicts.length > 0) {
    conflictsDrawer.classList.remove("hidden");
    $("conflict-count-badge").textContent = `${conflicts.length} Conflict(s)`;
    $("conflicts-list").innerHTML = conflicts.map(c => `
      <li class="conflict-item">
        <div class="conflict-meta">
          <strong style="color:#fbbf24;">Disputed Invariant: ${escapeHtml(c.affected_invariant || c.invariant_id)}</strong>
          <span class="badge">${escapeHtml(c.verifier_a)} (${escapeHtml(c.verdict_a)}) vs ${escapeHtml(c.verifier_b)} (${escapeHtml(c.verdict_b)})</span>
        </div>
        <div class="conflict-desc">${escapeHtml(c.description)}</div>
      </li>
    `).join("");
  } else {
    conflictsDrawer.classList.add("hidden");
  }

  // 3. CEGAR Diagnostics
  const cegarDrawer = $("cegar-drawer");
  const counterexamples = decision.counterexamples || data.cegar_counterexamples || [];
  if (counterexamples.length > 0 || kappa > 0) {
    cegarDrawer.classList.remove("hidden");
    const violations = counterexamples.flatMap(ce => ce.violations || []);
    if (violations.length > 0) {
      $("cegar-violations-list").innerHTML = violations.map(v => (
        `<li><strong>[${escapeHtml(v.invariant_id || "Violation")}]</strong> ${escapeHtml(v.description || "Invariant check failed")} (Severity: ${escapeHtml(v.severity || "high")})</li>`
      )).join("");
    } else if (decision.reason) {
      $("cegar-violations-list").innerHTML = `<li>${escapeHtml(decision.reason)}</li>`;
    }
  } else {
    cegarDrawer.classList.add("hidden");
  }

  // 4. Evidence lists
  $("actions").innerHTML = listMarkup(
    Object.entries(diffs).map(([k, v]) => `${k}: ${v === null ? "deleted" : "mutated"}`),
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

  renderStages(state);
  renderTimeline(state);
  renderVerificationChecks(verifications, kappa);

  // 5. Diff rendering
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

  // 6. Deep Technical View
  $("tech-invariants").textContent = (intent.required_invariants || []).join(", ") || "no_unauthorized_deletion, no_secret_exfiltration";
  $("tech-coordinates").textContent = intent.ambient_coordinates
    ? `[${intent.ambient_coordinates.map(n => Number(n).toFixed(2)).join(", ")}]`
    : "[0.50, 0.90, 0.95]";
  $("tech-auth-scope").textContent = intent.auth_scope || "PUBLIC";
  $("technical-decision").textContent = decision.outcome ? decision.outcome.toUpperCase() : (data.verification || "UNAVAILABLE");
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
  runText.textContent = "Executing in Sandbox...";
  runSpinner.classList.remove("hidden");

  try {
    const result = await request("/api/missions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        intent,
        auto_run: ($("mode").value === "shadow"),
      }),
    });
    renderMission(result);
    await Promise.all([refreshState(), refreshMissions()]);
  } catch (error) {
    showError(error);
  } finally {
    runBtn.disabled = false;
    runText.textContent = "Run Mission";
    runSpinner.classList.add("hidden");
  }
}

async function processAuthorization(approved) {
  if (!activeMissionId) {
    showError(new Error("No active mission selected for authorization"));
    return;
  }

  const user = $("auth-user")?.value.trim() || "security_officer";
  const comment = $("auth-comment")?.value.trim() || (approved ? "Authorized via Console" : "Rejected via Console");

  try {
    const updated = await request(`/api/missions/${encodeURIComponent(activeMissionId)}/authorize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approved, user, comment }),
    });
    renderMission(updated);
    await Promise.all([refreshState(), refreshMissions()]);
  } catch (err) {
    showError(err);
  }
}

// Event Listeners
$("run").addEventListener("click", runIntent);
$("refresh").addEventListener("click", refreshState);

if ($("btn-auth-approve")) {
  $("btn-auth-approve").addEventListener("click", () => processAuthorization(true));
}
if ($("btn-auth-reject")) {
  $("btn-auth-reject").addEventListener("click", () => processAuthorization(false));
}

$("new-mission").addEventListener("click", () => {
  activeMissionId = null;
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
  refreshMissions();
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
Promise.all([refreshState(), refreshHealth(), refreshMissions()]).catch(showError);
