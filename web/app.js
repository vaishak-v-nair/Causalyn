const $ = (id) => document.getElementById(id);

async function request(path, options) {
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Request failed");
  return payload;
}

function renderState(state) {
  $("state").textContent = `${state.file_count} files · ${Object.keys(state.data).length} data values`;
  $("files").innerHTML = state.files.map((file) => `<li>${file}</li>`).join("");
}

async function refreshState() {
  renderState(await request("/api/state"));
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
    await refreshState();
  } catch (error) {
    $("error").textContent = error.message;
  } finally {
    $("run").disabled = false;
  }
}

$("run").addEventListener("click", runIntent);
$("refresh").addEventListener("click", refreshState);
refreshState().catch((error) => { $("error").textContent = error.message; });
