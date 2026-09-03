const $ = (id) => document.getElementById(id);

async function request(path, options) {
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error?.message || payload.error || "Request failed");
  return payload;
}

function renderState(state) {
  $("state").textContent = `${state.file_count} files · ${Object.keys(state.data).length} data values`;
  $("files").innerHTML = state.files.map((file) => `<li><span class="file-icon">↳</span><code>${file}</code></li>`).join("");
}

async function refreshState() {
  renderState(await request("/api/state"));
}

async function refreshHealth() {
  await request("/api/health");
  $("health-dot").classList.add("online");
  $("health-text").textContent = "Local gate online";
}

async function refreshPipelines() {
  const payload = await request("/api/pipelines");
  const items = payload.pipelines || [];
  $("pipelines").innerHTML = items.length
    ? items.map((item) => `<li><div class="history-row"><code>${item.pipeline_id}</code><span class="history-status">${item.commit?.decision || item.stage}</span></div><span class="history-intent">${item.intent?.goal || "Untranslated intent"}</span></li>`).join("")
    : '<li class="muted">No pipeline runs yet.</li>';
}

function renderStages(stages) {
  const labels = ["intent_received", "intent_translated", "shadow_execution", "verification", "commit_attempt", "committed"];
  $("stages").innerHTML = labels.map((stage) => {
    const done = stages.includes(stage);
    return `<span class="${done ? "done" : ""}">${stage.replaceAll("_", " ")}</span>`;
  }).join("");
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
      body: JSON.stringify({intent})
    });
    $("result").classList.remove("hidden");
    $("stage").textContent = result.stage;
    $("pipeline").textContent = result.pipeline_id;
    $("goal").textContent = result.intent?.goal || "No intent specification";
    $("verification").textContent = result.verification || "not run";
    $("commit").textContent = result.commit?.decision || "not run";
    $("reason").textContent = result.commit?.reason || result.error || "";
    $("reason").classList.toggle("hidden", !result.commit?.reason && !result.error);
    renderStages(result.stages_completed || []);
    await Promise.all([refreshState(), refreshPipelines()]);
  } catch (error) {
    $("error").textContent = error.message;
  } finally {
    $("run").disabled = false;
  }
}

$("run").addEventListener("click", runIntent);
$("refresh").addEventListener("click", refreshState);
$("intent").addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") runIntent();
});
Promise.all([refreshState(), refreshHealth(), refreshPipelines()]).catch((error) => { $("error").textContent = error.message; });
