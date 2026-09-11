// Quansio V9 web client (UX-006): chat-first thin projection over canonical
// commands/events. A conversation IS a run: the user's objective is a user
// bubble, every visible state change is an assistant bubble rendered from a
// canonical event, and artifacts render as chips. There is no local
// task-state mutation path — commands go through quansio-api, and offline
// mode shows the last received snapshot with an explicit degraded marker,
// never a fabricated status.
"use strict";

const API = localStorage.getItem("quansio.api") || "http://127.0.0.1:8080";
const RUNTIME = localStorage.getItem("quansio.runtime") || "http://127.0.0.1:8087";
const CONTROL = localStorage.getItem("quansio.control") || "http://127.0.0.1:8081";
const ARTIFACT = localStorage.getItem("quansio.artifact") || "http://127.0.0.1:8088";

const state = {
  token: sessionStorage.getItem("quansio.token") || null,
  identity: JSON.parse(sessionStorage.getItem("quansio.identity") || "null"),
  runs: JSON.parse(localStorage.getItem("quansio.runs") || "{}"), // run_id -> {objective, status, thread:[{kind, text, tag}]}
  activeRun: localStorage.getItem("quansio.activeRun") || null,
  cursor: {},       // run_id -> last applied sequence
  followTimer: null,
};

function persistRuns() {
  localStorage.setItem("quansio.runs", JSON.stringify(state.runs));
  if (state.activeRun) localStorage.setItem("quansio.activeRun", state.activeRun);
}

async function call(service, path, options = {}) {
  const response = await fetch(service + path, {
    ...options,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...(options.headers || {}) },
  });
  const body = response.status === 204 ? {} : await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(`${response.status}: ${body.detail || response.statusText}`);
  return body;
}

function authHeaders() {
  return state.token ? { Authorization: `Bearer ${state.token}` } : {};
}

function setConnection(online) {
  const el = document.getElementById("connection");
  el.classList.toggle("online", online);
  el.classList.toggle("offline", !online);
  el.textContent = ""; // dot only; the tooltip carries the state
  el.title = online ? "online" : "offline — showing last received events only";
}

// -- thread rendering --------------------------------------------------------

function threadEl() {
  return document.getElementById("thread");
}

function renderThread() {
  const host = threadEl();
  host.innerHTML = "";
  const run = state.activeRun ? state.runs[state.activeRun] : null;
  if (!run || !run.thread.length) {
    host.innerHTML = `
      <div class="thread-empty">
        <h1>What should Quansio do?</h1>
        <p class="muted">Describe a task. Commands are admitted by quansio-api,
        executed by the canonical runtime, and every state change arrives here
        as a signed event.</p>
      </div>`;
    return;
  }
  const inner = document.createElement("div");
  inner.className = "thread-inner";
  for (const item of run.thread) {
    const wrap = document.createElement("div");
    wrap.className = `msg ${item.kind}`;
    const bubble = document.createElement("div");
    bubble.className = "bubble" + (item.error ? " error" : "");
    if (item.tag) {
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = item.tag;
      bubble.appendChild(tag);
    }
    bubble.appendChild(document.createTextNode(item.text));
    if (item.meta) {
      const meta = document.createElement("span");
      meta.className = "meta";
      meta.textContent = item.meta;
      bubble.appendChild(meta);
    }
    if (item.digest) {
      const chip = document.createElement("a");
      chip.className = "artifact-chip";
      chip.textContent = `artifact ${item.digest.slice(0, 16)}…`;
      chip.href = "#";
      chip.addEventListener("click", async (event) => {
        event.preventDefault();
        try {
          const meta = await call(ARTIFACT, `/v9/artifacts/${item.digest}/metadata`);
          chip.textContent = JSON.stringify(meta.metadata);
        } catch (error) {
          chip.textContent = `artifact lookup refused: ${error.message}`;
        }
      });
      bubble.appendChild(chip);
    }
    wrap.appendChild(bubble);
    inner.appendChild(wrap);
  }
  host.appendChild(inner);
  host.scrollTop = host.scrollHeight;
}

function pushThread(kind, text, extra = {}) {
  const run = state.runs[state.activeRun];
  if (!run) return;
  run.thread.push({ kind, text, ...extra });
  persistRuns();
  renderThread();
}

// -- runs sidebar --------------------------------------------------------------

function renderRunList() {
  const host = document.getElementById("run-list");
  host.innerHTML = "";
  const entries = Object.entries(state.runs).sort((a, b) => (b[1].created || 0) - (a[1].created || 0));
  for (const [runId, run] of entries) {
    const button = document.createElement("button");
    button.className = "run-item" + (runId === state.activeRun ? " active" : "");
    const title = document.createElement("span");
    title.textContent = (run.objective || runId).slice(0, 34);
    const status = document.createElement("span");
    status.className = "status";
    status.textContent = run.status || "";
    button.append(title, status);
    button.addEventListener("click", () => {
      state.activeRun = runId;
      persistRuns();
      renderThread();
      renderRunList();
      followActive();
    });
    host.appendChild(button);
  }
}

// -- canonical event application -------------------------------------------------

function applyEvent(runId, event) {
  const run = state.runs[runId];
  if (!run) return false;
  const cursor = state.cursor[runId] || 0;
  if (event.sequence <= cursor) return false;
  if (cursor && event.sequence > cursor + 1) return false; // gap: wait, never guess
  state.cursor[runId] = event.sequence;
  const payload = event.payload || {};
  if (event.event_type === "run.started") {
    run.thread.push({ kind: "bot", tag: "runtime", text: "Task accepted. Durable run admitted and dispatched.", meta: `run ${runId.slice(0, 8)} · seq ${event.sequence}` });
  } else if (event.event_type === "run.state" && payload.status === "succeeded" && payload.artifact_digest) {
    run.thread.push({ kind: "bot", tag: "result", text: "Done — result stored as an artifact.", digest: payload.artifact_digest, meta: `seq ${event.sequence}` });
  } else if (event.event_type === "run.state") {
    run.thread.push({ kind: "bot", tag: "runtime", text: `State: ${payload.status}${payload.detail ? ` — ${JSON.stringify(payload.detail)}` : ""}`, meta: `seq ${event.sequence}` });
  } else if (event.event_type === "turn.completed") {
    const answer = payload.result && (payload.result.answer ?? JSON.stringify(payload.result));
    run.thread.push({ kind: "bot", tag: "worker", text: String(answer ?? "step completed"), meta: `seq ${event.sequence}` });
  } else if (payload.status) {
    run.thread.push({ kind: "bot", tag: event.event_type, text: JSON.stringify(payload), meta: `seq ${event.sequence}` });
  }
  if (payload.status) run.status = payload.status;
  return true;
}

async function followActive() {
  const runId = state.activeRun;
  if (!runId || !state.token) return;
  try {
    const after = state.cursor[runId] || 0;
    const result = await call(RUNTIME, `/v9/events?run_id=${encodeURIComponent(runId)}&after_sequence=${after}`);
    let changed = false;
    for (const event of result.events) changed = applyEvent(runId, event) || changed;
    if (changed) {
      persistRuns();
      renderThread();
      renderRunList();
    }
    setConnection(true);
  } catch (error) {
    setConnection(false); // degraded: last snapshot stays, no invention
  }
}

function startFollowing() {
  if (state.followTimer) clearInterval(state.followTimer);
  state.followTimer = setInterval(followActive, 2000);
}

// -- auth ---------------------------------------------------------------------

function renderIdentity() {
  document.getElementById("whoami").textContent = state.identity
    ? `${state.identity.user_id.slice(0, 8)}`
    : "";
}

function show(view) {
  for (const section of document.querySelectorAll(".view")) section.hidden = true;
  if (!state.token) {
    document.getElementById("login-view").hidden = false;
    return;
  }
  const target = document.getElementById(`${view}-view`);
  if (target) target.hidden = false;
}

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
    show("thread");
    startFollowing();
  } catch (error) {
    document.getElementById("login-error").textContent = `sign-in refused: ${error.message}`;
  }
});

document.getElementById("logout").addEventListener("click", async () => {
  try { await call(API, "/v9/sessions/current", { method: "DELETE" }); } catch {}
  sessionStorage.removeItem("quansio.token");
  sessionStorage.removeItem("quansio.identity");
  state.token = null;
  state.identity = null;
  show("login");
});

// -- composer -------------------------------------------------------------------

document.getElementById("composer").addEventListener("submit", async (event) => {
  event.preventDefault();
  const objective = document.getElementById("objective").value.trim();
  const agentId = document.getElementById("agent-id").value.trim();
  const budget = Number(document.getElementById("budget").value || 0);
  if (!objective || !agentId) {
    if (!state.activeRun) {
      // Surface the requirement as an assistant-style message.
      document.querySelector(".thread-empty h1").textContent = "An admitted agent id is required";
      document.querySelector(".thread-empty .muted").textContent =
        "Admit a teammate first (control → capability snapshot → agent), then paste its id below the composer.";
    }
    return;
  }
  try {
    const result = await call(API, "/v9/commands", {
      method: "POST",
      body: JSON.stringify({
        command_type: "task.start",
        arguments: { objective, agent_id: agentId, budget_cents: budget },
        idempotency_key: `web-${crypto.randomUUID()}`,
      }),
    });
    const runId = result.run_id;
    state.runs[runId] = {
      objective, status: "running", created: Date.now(),
      thread: [{ kind: "user", text: objective, meta: `command ${result.command.command_id.slice(0, 8)}` }],
    };
    state.cursor[runId] = 0;
    state.activeRun = runId;
    persistRuns();
    document.getElementById("objective").value = "";
    renderRunList();
    renderThread();
    followActive();
  } catch (error) {
    if (state.activeRun) pushThread("bot", `Command refused: ${error.message}`, { error: true, tag: "api" });
    else alert(`command refused: ${error.message}`);
  }
});

document.getElementById("new-task").addEventListener("click", () => {
  state.activeRun = null;
  persistRuns();
  renderThread();
  renderRunList();
  document.getElementById("objective").focus();
});

// -- approvals + artifacts ---------------------------------------------------------

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

document.getElementById("nav-approvals").addEventListener("click", () => show("approvals"));
document.getElementById("nav-artifacts").addEventListener("click", () => show("artifacts"));
document.getElementById("new-task").addEventListener("click", () => show("thread"));

// -- boot -----------------------------------------------------------------------

renderIdentity();
renderRunList();
renderThread();
show(state.token ? "thread" : "login");
if (state.token) startFollowing();
