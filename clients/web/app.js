// Quansio V9 web client (UX-006): thin projection over canonical
// commands/events. All state changes come from the server; this script only
// renders and forwards user intent as admitted commands. There is no local
// task-state mutation path — offline mode renders the last snapshot and an
// explicit degraded banner, never a fabricated status.
"use strict";

const API = localStorage.getItem("quansio.api") || "http://127.0.0.1:8080";
const RUNTIME = localStorage.getItem("quansio.runtime") || "http://127.0.0.1:8087";
const CONTROL = localStorage.getItem("quansio.control") || "http://127.0.0.1:8081";
const ARTIFACT = localStorage.getItem("quansio.artifact") || "http://127.0.0.1:8088";

const state = {
  token: sessionStorage.getItem("quansio.token") || null,
  identity: JSON.parse(sessionStorage.getItem("quansio.identity") || "null"),
  timeline: [],      // canonical events in received order
  cursor: 0,
  taskStatus: {},    // run_id -> latest declared status from canonical events
};

function authHeaders() {
  return state.token ? { Authorization: `Bearer ${state.token}` } : {};
}

async function call(service, path, options = {}) {
  const response = await fetch(service + path, {
    ...options,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...(options.headers || {}) },
  });
  const body = response.status === 204 ? {} : await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(`${response.status}: ${body.detail || response.statusText}`);
  }
  return body;
}

function setConnection(online) {
  const el = document.getElementById("connection");
  el.textContent = online ? "online" : "offline";
  el.className = online ? "online" : "offline";
}

function renderIdentity() {
  document.getElementById("whoami").textContent = state.identity
    ? `${state.identity.user_id.slice(0, 8)} · ${state.identity.roles.join(",")}`
    : "";
}

function applyEvent(event) {
  // Canonical events are the only source of task state; duplicates and gaps
  // are dropped, never guessed.
  if (event.sequence <= state.cursor) return false;
  if (state.cursor && event.sequence > state.cursor + 1) return false;
  state.cursor = event.sequence;
  state.timeline.push(event);
  if (event.payload && event.payload.status) {
    state.taskStatus[event.run_id] = event.payload.status;
  }
  return true;
}

function renderTimeline() {
  const list = document.getElementById("timeline");
  list.innerHTML = "";
  for (const event of state.timeline.slice(-50)) {
    const li = document.createElement("li");
    li.textContent = `#${event.sequence} ${event.run_id.slice(0, 8)} ${event.event_type} ${JSON.stringify(event.payload)}`;
    list.appendChild(li);
  }
}

function show(view) {
  for (const section of document.querySelectorAll(".view, #view-login")) {
    section.hidden = section.id !== `view-${view}`;
  }
  if (!state.token) {
    document.querySelectorAll(".view").forEach((s) => (s.hidden = true));
    document.getElementById("view-login").hidden = false;
    return;
  }
  document.getElementById("view-login").hidden = true;
}

// -- login ------------------------------------------------------------------

document.getElementById("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    const result = await call(API, "/v9/sessions", {
      method: "POST",
      body: JSON.stringify(Object.fromEntries(form)),
    });
    state.token = result.token;
    state.identity = result.identity;
    sessionStorage.setItem("quansio.token", result.token);
    sessionStorage.setItem("quansio.identity", JSON.stringify(result.identity));
    document.getElementById("login-error").textContent = "";
    renderIdentity();
    show("tasks");
  } catch (error) {
    document.getElementById("login-error").textContent = `sign-in refused: ${error.message}`;
  }
});

// -- commands ----------------------------------------------------------------

document.getElementById("task-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    const result = await call(API, "/v9/commands", {
      method: "POST",
      body: JSON.stringify({
        command_type: "task.start",
        arguments: {
          objective: form.get("objective"),
          agent_id: form.get("agent_id") || undefined,
          budget_cents: Number(form.get("budget_cents") || 0),
        },
        idempotency_key: `web-${crypto.randomUUID()}`,
      }),
    });
    // The runtime admission returns the durable run the command produced;
    // the timeline follows that run — never the command id.
    document.getElementById("run-id").value = result.run_id;
  } catch (error) {
    alert(`command refused: ${error.message}`);
  }
});

document.getElementById("follow").addEventListener("click", async () => {
  const runId = document.getElementById("run-id").value.trim();
  if (!runId) return;
  try {
    const result = await call(RUNTIME, `/v9/events?run_id=${encodeURIComponent(runId)}&after_sequence=${state.cursor}`);
    let changed = false;
    for (const event of result.events) changed = applyEvent(event) || changed;
    if (changed) renderTimeline();
    setConnection(true);
  } catch (error) {
    setConnection(false); // degraded: last snapshot stays, no invention
  }
});

// -- approvals ----------------------------------------------------------------

document.getElementById("approval-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const approvalId = new FormData(event.target).get("approval_id");
  const decision = event.submitter?.value || "deny";
  try {
    const result = await call(CONTROL, `/v9/approvals/${encodeURIComponent(approvalId)}/decision`, {
      method: "POST",
      body: JSON.stringify({ approved: decision === "approve", approver_id: state.identity.user_id }),
    });
    document.getElementById("approval-result").textContent = JSON.stringify(result);
  } catch (error) {
    document.getElementById("approval-result").textContent = `refused: ${error.message}`;
  }
});

// -- artifacts ----------------------------------------------------------------

document.getElementById("artifact-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const digest = new FormData(event.target).get("digest");
  try {
    const result = await call(ARTIFACT, `/v9/artifacts/${encodeURIComponent(digest)}/metadata`);
    document.getElementById("artifact-result").textContent = JSON.stringify(result, null, 2);
  } catch (error) {
    document.getElementById("artifact-result").textContent = `refused: ${error.message}`;
  }
});

// -- navigation ----------------------------------------------------------------

document.querySelectorAll("nav button").forEach((button) => {
  button.addEventListener("click", () => show(button.dataset.view));
});

renderIdentity();
show(state.token ? "tasks" : "login");
