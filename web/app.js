const $ = (id) => document.getElementById(id);
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
}[char]));

async function request(path, options) {
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error?.message || payload.error || "Request failed");
  return payload;
}

function listMarkup(items, empty) {
  const values = (items || []).filter(Boolean);
  return values.length ? values.map((item) => `<li>${escapeHtml(item)}</li>`).join("") : `<li class="muted">${escapeHtml(empty)}</li>`;
}

function renderState(state) {
  $("state").textContent = `${state.file_count} files · ${Object.keys(state.data || {}).length} data values`;
  $("files").innerHTML = (state.files || []).map((file) => `<li><span class="file-icon">↳</span><code>${escapeHtml(file)}</code></li>`).join("");
}

async function refreshState() {
  renderState(await request("/api/state"));
}

async function refreshHealth() {
  await request("/api/health");
  $("health-dot").classList.add("online");
  $("health-text").textContent = "Local gate online";
}

function renderHistory(items) {
  $("pipelines").innerHTML = items.length
    ? items.map((item) => `<li><button class="history-link" data-pipeline="${escapeHtml(item.pipeline_id)}"><span class="history-row"><code>${escapeHtml(item.pipeline_id)}</code><span class="history-status">${escapeHtml(item.commit?.decision || item.stage)}</span></span><span class="history-intent">${escapeHtml(item.intent?.goal || "Untranslated intent")}</span></button></li>`).join("")
    : '<li class="muted">No pipeline runs yet.</li>';
  document.querySelectorAll("[data-pipeline]").forEach((button) => {
    button.addEventListener("click", () => request(`/api/pipelines/${encodeURIComponent(button.dataset.pipeline)}`).then(renderResult).catch(showError));
  });
}

async function refreshPipelines() {
  const payload = await request("/api/pipelines");
  renderHistory(payload.pipelines || []);
}

function renderStages(stages) {
  const lifecycle = [
    ["intent_translated", "Analyze"],
    ["shadow_execution", "Shadow"],
    ["verification", "Verify"],
    ["commit_attempt", "Authorize"],
    ["committed", "Commit"],
  ];
  $("stages").innerHTML = lifecycle.map(([stage, label]) => `<span class="${stages.includes(stage) ? "done" : ""}">${label}</span>`).join("");
}

function renderResult(result) {
  const intent = result.intent || {};
  const commit = result.commit || {};
  $("result").classList.remove("hidden");
  $("stage").textContent = result.stage || "unknown";
  $("pipeline").textContent = result.pipeline_id || "";
  $("goal").textContent = intent.goal || "No intent specification";
  $("verification").textContent = result.verification || "not run";
  $("commit").textContent = commit.decision || "not run";
  $("authorization").textContent = commit.authorization_given === true ? "Granted" : commit.authorization_given === false ? "Not granted" : "Not evaluated";
  $("changes").textContent = commit.changes ? Object.keys(commit.changes).length : "0";
  $("authorization-detail").textContent = commit.authorization_given === true ? "This run has an authorization decision from the commit boundary." : "Commit authorization was not granted by the API.";
  $("commit-id").textContent = commit.commit_id || "";
  $("reason").textContent = commit.reason || result.error || "";
  $("reason").classList.toggle("hidden", !commit.reason && !result.error);
  $("actions").innerHTML = listMarkup(Object.entries(commit.changes || {}).map(([key, value]) => `${key}: ${value === null ? "removed" : "updated"}`), "No state changes recorded.");
  $("risks").innerHTML = listMarkup([...(intent.ambiguities || []), ...(intent.unknowns || []), ...(intent.forbidden_states || [])], "None reported by the API.");
  $("assumptions").innerHTML = listMarkup(intent.assumptions, "None reported by the API.");
  renderStages(result.stages_completed || []);
}

function showError(error) {
  $("error").textContent = error.message || String(error);
}

async function runIntent() {
  const intent = $("intent").value.trim();
  $("error").textContent = "";
  if (!intent) { $("error").textContent = "Enter an intent first."; return; }
  $("run").disabled = true;
  try {
    const result = await request("/api/intents", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({intent, execution_mode: $("mode").value})
    });
    renderResult(result);
    await Promise.all([refreshState(), refreshPipelines()]);
  } catch (error) {
    showError(error);
  } finally {
    $("run").disabled = false;
  }
}

$("run").addEventListener("click", runIntent);
$("refresh").addEventListener("click", refreshState);
$("intent").addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") runIntent();
});
Promise.all([refreshState(), refreshHealth(), refreshPipelines()]).catch(showError);
