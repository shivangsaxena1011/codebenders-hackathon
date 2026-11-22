let currentRole = localStorage.getItem("carerelay_role") || "remote";
let latestData = null;

const roleSelect = document.getElementById("roleSelect");
if (roleSelect) {
  roleSelect.value = currentRole;
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}

async function api(path, options = {}) {
  const headers = Object.assign(
    { "Content-Type": "application/json", "X-Care-Role": currentRole },
    options.headers || {}
  );
  try {
    const res = await fetch(path, { ...options, headers });
    let data;
    try {
      data = await res.json();
    } catch {
      data = { error: `Server error (${res.status})` };
    }
    if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
    return data;
  } catch (err) {
    throw err;
  }
}

async function loadDashboard() {
  try {
    const data = await api("/api/dashboard");
    latestData = data;
    localStorage.setItem("carerelay_offline_cache", JSON.stringify(data));
    render(data);
  } catch (err) {
    const cached = localStorage.getItem("carerelay_offline_cache");
    if (cached) {
      latestData = JSON.parse(cached);
      render(latestData);
      showNotice("Working offline: showing cached care snapshot.");
    } else {
      showNotice(`Error loading care hub: ${err.message}`, true);
    }
  }
}

function showNotice(msg, isError = false) {
  let banner = document.getElementById("liveNoticeBanner");
  if (!banner) {
    banner = document.createElement("div");
    banner.id = "liveNoticeBanner";
    document.body.prepend(banner);
  }
  banner.className = `notice-banner ${isError ? "error" : "info"}`;
  banner.textContent = msg;
  setTimeout(() => {
    if (banner) banner.remove();
  }, 4000);
}

function render(data) {
  const perms = new Set(data.role.permissions || []);
  document.getElementById("patientBanner").textContent =
    `${data.patient.name} • Age ${data.patient.age} • ${data.patient.city} | Viewing as: ${data.role.label}`;

  // RBAC Section Visibility
  toggle("pulseSection", perms.has("view_pulse"));
  toggle("extractorSection", perms.has("ingest_records"));
  toggle("tasksSection", perms.has("view_tasks"));
  toggle("refillsSection", perms.has("view_refills"));
  toggle("timelineSection", perms.has("view_timeline"));
  toggle("fairnessSection", perms.has("view_fairness"));
  toggle("auditSection", perms.has("view_audit"));
  toggle("btnNewTaskToggle", perms.has("manage_tasks"));
  toggle("btnNewRefillToggle", perms.has("manage_refills"));
  toggle("btnNewTimelineToggle", perms.has("ingest_records"));
  toggle("btnDoctorBrief", perms.has("view_doctor_brief"));

  // 1. 10-Second Pulse Briefing
  if (perms.has("view_pulse")) {
    const urgentRefills = (data.refills || []).filter(
      (r) => r.days_left <= 5 && r.claim_status === "unclaimed"
    );
    const backupTasks = (data.tasks || []).filter(
      (t) => t.needs_backup === 1 && t.status === "pending"
    );
    const urgentTotal = urgentRefills.length + backupTasks.length;

    document.getElementById("pulseUrgentCount").textContent =
      urgentTotal === 0 ? "All Clear" : `${urgentTotal} Action Needed`;

    const urgentParts = [];
    if (urgentRefills.length) {
      urgentParts.push(`${urgentRefills[0].medicine_name} (${urgentRefills[0].days_left}d left)`);
    }
    if (backupTasks.length) {
      urgentParts.push(`Backup needed: ${backupTasks[0].title}`);
    }
    document.getElementById("pulseUrgentText").textContent =
      urgentParts.length ? urgentParts.join(" • ") : "No overdue refills or active backup requests.";

    const pendingTasks = (data.tasks || []).filter((t) => t.status === "pending");
    const owners = [...new Set(pendingTasks.map((t) => t.assigned_to))];
    document.getElementById("pulseOnPointCount").textContent = `${pendingTasks.length} Pending`;
    document.getElementById("pulseOnPointText").textContent =
      owners.length ? `On point: ${owners.join(", ")}` : "All scheduled care tasks are complete.";

    const latest = (data.audit_logs || [])[0];
    document.getElementById("pulseLatestAction").textContent = latest ? latest.actor_name : "—";
    document.getElementById("pulseLatestText").textContent =
      latest ? `${latest.summary} (${latest.created_at.replace("T", " ")})` : "No activity recorded yet.";
  }

  // 2. Tasks Rendering (Pending first, then completed)
  const tasksEl = document.getElementById("tasksList");
  tasksEl.innerHTML = "";
  if (!data.tasks || !data.tasks.length) {
    tasksEl.innerHTML = `<p class="muted">No tasks visible for this role.</p>`;
  } else {
    data.tasks.forEach((t) => {
      const div = document.createElement("div");
      div.className = `item ${t.needs_backup ? "backup" : ""} ${t.status === "completed" ? "done" : ""}`;
      
      const badge = t.status === "completed"
        ? `<span class="badge badge-ok">Completed</span>`
        : t.needs_backup
          ? `<span class="badge badge-urgent">Needs Sibling Backup</span>`
          : `<span class="badge badge-info">Pending</span>`;

      const expenseNote = t.expense_inr > 0 ? ` • Paid: ₹${Math.round(t.expense_inr)}` : "";
      const completedNote = t.completed_by ? ` • By: ${escapeHtml(t.completed_by)}` : "";

      let actionsHtml = "";
      if (t.status === "pending") {
        actionsHtml += `<button class="btn btn-primary btn-small" onclick="openCompleteTaskModal(${t.id}, '${escapeJsString(t.title)}')">Mark Done</button>`;
        if (perms.has("manage_tasks")) {
          if (t.needs_backup) {
            actionsHtml += `<button class="btn btn-warn btn-small" onclick="taskAction(${t.id}, 'claim')">Claim Task</button>`;
            actionsHtml += `<button class="btn btn-outline btn-small" onclick="taskAction(${t.id}, 'cancel_backup')">Cancel Backup</button>`;
          } else {
            actionsHtml += `<button class="btn btn-outline btn-small" onclick="taskAction(${t.id}, 'backup')">Need Backup</button>`;
          }
        }
      }

      div.innerHTML = `
        <div>
          <div class="item-title">${escapeHtml(t.title)} ${badge}</div>
          <div class="item-meta">Owner: <strong>${escapeHtml(t.assigned_to)}</strong> • Due: ${escapeHtml(t.due_date)}${expenseNote}${completedNote}</div>
          ${t.completion_note ? `<div class="item-meta item-note">Note: ${escapeHtml(t.completion_note)}</div>` : ""}
        </div>
        <div class="item-actions">${actionsHtml}</div>
      `;
      tasksEl.appendChild(div);
    });
  }

  // 3. Smart Refill Runway Rendering (Sorted by days_left)
  const refillsEl = document.getElementById("refillsList");
  refillsEl.innerHTML = "";
  if (!data.refills || !data.refills.length) {
    refillsEl.innerHTML = `<p class="muted">No medication refills tracked.</p>`;
  } else {
    data.refills.forEach((r) => {
      const div = document.createElement("div");
      div.className = "item";

      let statusBadge = "";
      if (r.claim_status === "ordered") {
        statusBadge = `<span class="badge badge-warn">Ordered by ${escapeHtml(r.claimed_by)} (${r.days_left}d left)</span>`;
      } else if (r.days_left <= 0) {
        statusBadge = `<span class="badge badge-urgent">OUT OF STOCK (0 days left)</span>`;
      } else if (r.days_left <= 5) {
        statusBadge = `<span class="badge badge-urgent">${r.days_left} days left</span>`;
      } else {
        statusBadge = `<span class="badge badge-ok">${r.days_left} days left</span>`;
      }

      let actions = "";
      if (perms.has("manage_refills")) {
        if (r.claim_status === "unclaimed") {
          actions += `<button class="btn btn-primary btn-small" onclick="claimRefill(${r.id})">Claim Refill</button>`;
        } else if (r.claim_status === "ordered") {
          actions += `<button class="btn btn-ok btn-small" onclick="openRestockModal(${r.id}, '${escapeJsString(r.medicine_name)}')">Mark Delivered (+30)</button>`;
        } else {
          actions += `<button class="btn btn-outline btn-small" onclick="openRestockModal(${r.id}, '${escapeJsString(r.medicine_name)}')">+ Add Stock</button>`;
        }
      }

      div.innerHTML = `
        <div>
          <div class="item-title">${escapeHtml(r.medicine_name)} ${statusBadge}</div>
          <div class="item-meta">${escapeHtml(r.dosage)} • ${r.tablets_remaining} tablets remaining • Daily: ${r.daily_units || 1}</div>
          <div class="item-meta">Source: ${escapeHtml(r.source_prescription)}${r.fulfillment_mode ? ` • ${escapeHtml(r.fulfillment_mode)}` : ""}</div>
        </div>
        <div class="item-actions">${actions}</div>
      `;
      refillsEl.appendChild(div);
    });
  }

  // 4. Shared Care Timeline Rendering
  const timelineEl = document.getElementById("timelineList");
  timelineEl.innerHTML = "";
  if (!data.timeline || !data.timeline.length) {
    timelineEl.innerHTML = `<p class="muted">No timeline events recorded.</p>`;
  } else {
    data.timeline.forEach((ev) => {
      const div = document.createElement("div");
      div.className = "item";
      div.innerHTML = `
        <div>
          <div class="item-title">${escapeHtml(ev.title)} <span class="badge badge-info">${escapeHtml(ev.event_type)}</span></div>
          <div class="item-meta">${escapeHtml(ev.event_date)} • ${escapeHtml(ev.provider_or_source)} • Logged by ${escapeHtml(ev.created_by)}</div>
          ${ev.details ? `<div class="item-meta">${escapeHtml(ev.details)}</div>` : ""}
        </div>
      `;
      timelineEl.appendChild(div);
    });
  }

  // 5. Care-Load & Expense Fairness Rendering
  const fairEl = document.getElementById("fairnessList");
  fairEl.innerHTML = "";
  if (!data.fairness || !data.fairness.length) {
    fairEl.innerHTML = `<p class="muted">Fairness metrics hidden for this role.</p>`;
  } else {
    data.fairness.forEach((f) => {
      const box = document.createElement("div");
      box.className = "fair-box";
      box.innerHTML = `
        <strong>${escapeHtml(f.member)}</strong>
        <span>${f.tasks_done} tasks completed • ${f.tasks_pending} pending</span>
        <div style="margin-top:6px; font-size:0.95rem; font-weight:700; color:var(--primary);">
          Out-of-Pocket: ₹${Math.round(f.total_inr || 0)}
        </div>
      `;
      fairEl.appendChild(box);
    });
  }

  // 6. Immutable Audit Ledger Rendering
  const auditEl = document.getElementById("auditList");
  auditEl.innerHTML = "";
  if (!data.audit_logs || !data.audit_logs.length) {
    auditEl.innerHTML = `<p class="muted">Audit logs hidden or empty.</p>`;
  } else {
    data.audit_logs.forEach((log) => {
      const row = document.createElement("div");
      row.className = "audit-row";
      row.innerHTML = `<strong>${escapeHtml(log.actor_name)}</strong> <span class="muted">(${escapeHtml(log.actor_role)})</span>: ${escapeHtml(log.summary)} <span class="muted">• ${escapeHtml(log.created_at.replace("T", " "))}</span>`;
      auditEl.appendChild(row);
    });
  }
}

function toggle(id, show) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle("hidden", !show);
}

function escapeHtml(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function escapeJsString(str) {
  return String(str || "").replace(/'/g, "\\'").replace(/"/g, '\\"');
}

// Role Switcher
roleSelect.addEventListener("change", (e) => {
  currentRole = e.target.value;
  localStorage.setItem("carerelay_role", currentRole);
  loadDashboard();
});

// Task Creation Form Handlers
document.getElementById("btnNewTaskToggle").addEventListener("click", () => {
  const form = document.getElementById("newTaskForm");
  form.classList.toggle("hidden");
  if (!form.classList.contains("hidden")) {
    document.getElementById("taskDue").value = new Date().toISOString().split("T")[0];
    document.getElementById("taskTitle").focus();
  }
});

document.getElementById("btnCancelTask").addEventListener("click", () => {
  document.getElementById("newTaskForm").classList.add("hidden");
});

document.getElementById("newTaskForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const title = document.getElementById("taskTitle").value.trim();
  const assigned_to = document.getElementById("taskAssignee").value;
  const due_date = document.getElementById("taskDue").value;

  try {
    await api("/api/tasks", {
      method: "POST",
      body: JSON.stringify({ title, assigned_to, due_date }),
    });
    e.target.reset();
    e.target.classList.add("hidden");
    loadDashboard();
  } catch (err) {
    alert(err.message);
  }
});

// Refill Creation Form Handlers
document.getElementById("btnNewRefillToggle").addEventListener("click", () => {
  const form = document.getElementById("newRefillForm");
  form.classList.toggle("hidden");
  if (!form.classList.contains("hidden")) {
    document.getElementById("refillMedName").focus();
  }
});

document.getElementById("btnCancelRefill").addEventListener("click", () => {
  document.getElementById("newRefillForm").classList.add("hidden");
});

document.getElementById("newRefillForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const medicine_name = document.getElementById("refillMedName").value.trim();
  const dosage = document.getElementById("refillDosage").value.trim();
  const tablets_remaining = parseInt(document.getElementById("refillTabs").value, 10) || 0;
  const daily_units = parseInt(document.getElementById("refillDaily").value, 10) || 1;

  try {
    await api("/api/refills", {
      method: "POST",
      body: JSON.stringify({ medicine_name, dosage, tablets_remaining, daily_units }),
    });
    e.target.reset();
    e.target.classList.add("hidden");
    loadDashboard();
  } catch (err) {
    alert(err.message);
  }
});

// Timeline Record Creation Handlers
document.getElementById("btnNewTimelineToggle").addEventListener("click", () => {
  const form = document.getElementById("newTimelineForm");
  form.classList.toggle("hidden");
  if (!form.classList.contains("hidden")) {
    document.getElementById("recordDate").value = new Date().toISOString().split("T")[0];
    document.getElementById("recordTitle").focus();
  }
});

document.getElementById("btnCancelTimeline").addEventListener("click", () => {
  document.getElementById("newTimelineForm").classList.add("hidden");
});

document.getElementById("newTimelineForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const event_type = document.getElementById("recordType").value;
  const title = document.getElementById("recordTitle").value.trim();
  const event_date = document.getElementById("recordDate").value;
  const provider_or_source = document.getElementById("recordSource").value.trim() || "Caregiver Verified Record";
  const details = document.getElementById("recordDetails").value.trim();
  const create_companion_task = document.getElementById("recordCompanionTask").checked;

  try {
    await api("/api/timeline", {
      method: "POST",
      body: JSON.stringify({
        event_type,
        title,
        event_date,
        provider_or_source,
        details,
        create_companion_task,
        assigned_to: currentRole === "remote" ? "Arjun Sharma" : "Priya Sharma",
      }),
    });
    e.target.reset();
    e.target.classList.add("hidden");
    loadDashboard();
  } catch (err) {
    alert(err.message);
  }
});

// Task Complete Modal
function openCompleteTaskModal(id, title) {
  document.getElementById("completeTaskId").value = id;
  document.getElementById("completeTaskSubtitle").textContent = `Task: ${title}`;
  document.getElementById("completeNote").value = "Completed as planned";
  document.getElementById("completeExpense").value = "0";

  // Hide expense field for attendant role
  const expenseGroup = document.getElementById("completeExpenseGroup");
  if (expenseGroup) {
    expenseGroup.style.display = currentRole === "attendant" ? "none" : "block";
  }

  document.getElementById("completeTaskModal").classList.remove("hidden");
}

document.getElementById("btnCloseCompleteModal").onclick = () => {
  document.getElementById("completeTaskModal").classList.add("hidden");
};
document.getElementById("btnCancelComplete").onclick = () => {
  document.getElementById("completeTaskModal").classList.add("hidden");
};

document.getElementById("completeTaskForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("completeTaskId").value;
  const note = document.getElementById("completeNote").value.trim();
  const expense_inr = parseFloat(document.getElementById("completeExpense").value) || 0;

  try {
    await api(`/api/tasks/${id}/action`, {
      method: "POST",
      body: JSON.stringify({ action: "complete", note, expense_inr }),
    });
    document.getElementById("completeTaskModal").classList.add("hidden");
    loadDashboard();
  } catch (err) {
    alert(err.message);
  }
});

// Restock Modal
function openRestockModal(id, medName) {
  document.getElementById("restockRefillId").value = id;
  document.getElementById("restockRefillSubtitle").textContent = `Medicine: ${medName}`;
  document.getElementById("restockTabsAdded").value = "30";
  document.getElementById("restockRefillModal").classList.remove("hidden");
}

document.getElementById("btnCloseRestockModal").onclick = () => {
  document.getElementById("restockRefillModal").classList.add("hidden");
};
document.getElementById("btnCancelRestock").onclick = () => {
  document.getElementById("restockRefillModal").classList.add("hidden");
};

document.getElementById("restockRefillForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = document.getElementById("restockRefillId").value;
  const tablets_added = parseInt(document.getElementById("restockTabsAdded").value, 10) || 30;

  try {
    await api(`/api/refills/${id}/restock`, {
      method: "POST",
      body: JSON.stringify({ tablets_added }),
    });
    document.getElementById("restockRefillModal").classList.add("hidden");
    loadDashboard();
  } catch (err) {
    alert(err.message);
  }
});

// Other Task Actions (Backup / Claim)
async function taskAction(id, action) {
  try {
    await api(`/api/tasks/${id}/action`, { method: "POST", body: JSON.stringify({ action }) });
    loadDashboard();
  } catch (err) {
    alert(err.message);
  }
}

// Claim Refill
async function claimRefill(id) {
  const mode = currentRole === "remote" ? "Online Order (Bengaluru -> Bhopal)" : "Local Pharmacy Pickup (Bhopal)";
  try {
    await api(`/api/refills/${id}/claim`, { method: "POST", body: JSON.stringify({ mode }) });
    loadDashboard();
  } catch (err) {
    alert(err.message);
  }
}

// Extractor & Guardrail Logic
document.querySelectorAll(".chip").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.getElementById("extractInput").value = btn.dataset.sample;
  });
});

document.getElementById("btnExtract").addEventListener("click", async () => {
  const inputEl = document.getElementById("extractInput");
  const text = inputEl.value.trim();
  if (!text) return;

  const btn = document.getElementById("btnExtract");
  btn.disabled = true;
  btn.textContent = "Parsing...";

  try {
    const res = await api("/api/extract", { method: "POST", body: JSON.stringify({ text }) });
    const prev = document.getElementById("extractPreview");
    prev.classList.remove("hidden", "blocked");

    if (res.blocked) {
      prev.classList.add("blocked");
      prev.innerHTML = `<strong>${escapeHtml(res.reason)}</strong>`;
      return;
    }

    const ex = res.extracted;
    prev.innerHTML = `
      <strong>Parsed Draft (${escapeHtml(ex.kind.toUpperCase())}) — Human Confirmation Required:</strong>
      <div style="margin: 6px 0;">Title: <strong>${escapeHtml(ex.title)}</strong> • Date: ${escapeHtml(ex.event_date || ex.due_date || "Today")}</div>
      ${ex.kind === "appointment" ? `<label style="font-size:0.8rem; display:block; margin-bottom:8px;"><input type="checkbox" id="extractEscortTask" checked /> Automatically create companion escort task</label>` : ""}
      <div style="margin-top:8px; display:flex; gap:6px;">
        <button class="btn btn-primary btn-small" id="btnConfirmExtract">Confirm &amp; Save to Hub</button>
        <button class="btn btn-outline btn-small" id="btnDiscardExtract">Discard</button>
      </div>
    `;

    document.getElementById("btnDiscardExtract").onclick = () => {
      prev.classList.add("hidden");
    };

    document.getElementById("btnConfirmExtract").onclick = async () => {
      const confirmBtn = document.getElementById("btnConfirmExtract");
      confirmBtn.disabled = true;
      confirmBtn.textContent = "Saving...";

      try {
        if (ex.kind === "appointment") {
          const createEscort = document.getElementById("extractEscortTask")?.checked;
          await api("/api/timeline", {
            method: "POST",
            body: JSON.stringify({
              event_type: "appointment",
              title: ex.title,
              event_date: ex.event_date,
              provider_or_source: ex.provider_or_source,
              details: ex.details,
              create_companion_task: createEscort,
              assigned_to: "Priya Sharma",
            }),
          });
        } else if (ex.kind === "refill") {
          await api("/api/refills", {
            method: "POST",
            body: JSON.stringify({
              medicine_name: ex.title,
              dosage: ex.dosage,
              tablets_remaining: ex.tablets_remaining,
              daily_units: ex.daily_units,
              source_prescription: ex.source_prescription,
            }),
          });
        } else {
          await api("/api/tasks", {
            method: "POST",
            body: JSON.stringify({
              title: ex.title,
              assigned_to: ex.assigned_to,
              due_date: ex.due_date,
            }),
          });
        }
        inputEl.value = "";
        prev.classList.add("hidden");
        loadDashboard();
      } catch (err) {
        alert(err.message);
        confirmBtn.disabled = false;
        confirmBtn.textContent = "Confirm & Save to Hub";
      }
    };
  } catch (err) {
    alert(err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Parse Note";
  }
});

// Doctor Visit Brief Modal
document.getElementById("btnDoctorBrief").addEventListener("click", () => {
  if (!latestData) return;
  const body = document.getElementById("briefBody");

  const medsHtml = (latestData.refills || []).length
    ? latestData.refills
        .map(
          (r) =>
            `<li><strong>${escapeHtml(r.medicine_name)}</strong> — ${escapeHtml(r.dosage)} (${r.tablets_remaining} tablets remaining; daily: ${r.daily_units || 1}) • <em>${escapeHtml(r.source_prescription)}</em></li>`
        )
        .join("")
    : "<li>No active medication records.</li>";

  const eventsHtml = (latestData.timeline || []).length
    ? latestData.timeline
        .map(
          (e) =>
            `<li><strong>${escapeHtml(e.event_date)}</strong> [${escapeHtml(e.event_type)}]: ${escapeHtml(e.title)} — <em>${escapeHtml(e.provider_or_source)}</em><br>${escapeHtml(e.details)}</li>`
        )
        .join("")
    : "<li>No timeline events recorded.</li>";

  body.innerHTML = `
    <div style="background:#f0fdf4; border:1px solid #bbf7d0; padding:10px; border-radius:8px; font-size:0.85rem; margin-bottom:14px;">
      <strong>Guardrail Notice:</strong> Factual care record organization only. Does not diagnose or recommend treatment. Clinical decisions rest solely with attending physicians.
    </div>
    <div style="margin-bottom:12px; font-size:0.9rem;">
      <strong>Patient:</strong> Ramesh Sharma (72, Male, Bhopal) • <strong>Primary Caregiver:</strong> Priya Sharma (Bhopal) • <strong>Remote Co-Manager:</strong> Arjun Sharma (Bengaluru)
    </div>
    <h3>Tracked Prescription Medications</h3>
    <ul>${medsHtml}</ul>
    <h3 style="margin-top:16px;">Verified Care Timeline &amp; Recent Reports</h3>
    <ul>${eventsHtml}</ul>
  `;

  document.getElementById("briefModal").classList.remove("hidden");
});

document.getElementById("btnCloseBrief").addEventListener("click", () => {
  document.getElementById("briefModal").classList.add("hidden");
});

// Close modals when clicking on backdrop or pressing ESC
window.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal")) {
    e.target.classList.add("hidden");
  }
});

window.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    document.querySelectorAll(".modal").forEach((m) => m.classList.add("hidden"));
  }
});

loadDashboard();
