#!/usr/bin/env python3
"""
CareRelay - The Family Care Hub (ACE Builders' Hackathon 2026 - PS 4)
Zero-dependency Python 3 + SQLite3 backend with role-based access control (RBAC),
immutable audit ledger, refill runway calculations, and extraction-only parser.
Synthetic demo data only. Organizes information only; never diagnoses.
"""

import json
import mimetypes
import os
import re
import sqlite3
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DB_PATH = os.path.join(BASE_DIR, "carerelay.db")

ROLES = {
    "primary": {
        "id": "primary",
        "name": "Priya Sharma",
        "label": "Primary Caregiver (Bhopal)",
        "city": "Bhopal",
        "permissions": [
            "view_pulse", "view_timeline", "view_tasks", "manage_tasks",
            "view_refills", "manage_refills", "view_fairness", "view_audit",
            "view_doctor_brief", "ingest_records", "manage_roles"
        ],
    },
    "remote": {
        "id": "remote",
        "name": "Arjun Sharma",
        "label": "Remote Co-Manager (Bengaluru)",
        "city": "Bengaluru",
        "permissions": [
            "view_pulse", "view_timeline", "view_tasks", "manage_tasks",
            "view_refills", "manage_refills", "view_fairness", "view_audit",
            "view_doctor_brief", "ingest_records"
        ],
    },
    "attendant": {
        "id": "attendant",
        "name": "Sunita Devi",
        "label": "Care Attendant (Task-Only)",
        "city": "Bhopal",
        "permissions": ["view_tasks", "complete_assigned_tasks"],
    },
    "doctor": {
        "id": "doctor",
        "name": "Dr. R. K. Verma",
        "label": "Doctor 24h Read-Only Pass",
        "city": "Bhopal",
        "permissions": ["view_timeline", "view_refills", "view_doctor_brief"],
    },
}

# Strict guardrail: block diagnostic assertions and direct dosage/treatment modifications
DIAGNOSTIC_BLOCKLIST = [
    "diagnose", "diagnosis", "stop taking", "increase dose",
    "decrease dose", "double dose", "cancer", "heart attack", "stroke risk",
    "you should take", "recommended treatment"
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS timeline_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            title TEXT NOT NULL,
            event_date TEXT NOT NULL,
            provider_or_source TEXT NOT NULL,
            details TEXT NOT NULL,
            created_by TEXT NOT NULL,
            visibility TEXT NOT NULL DEFAULT 'family',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            assigned_to TEXT NOT NULL,
            assigned_role TEXT NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            needs_backup INTEGER NOT NULL DEFAULT 0,
            expense_inr REAL NOT NULL DEFAULT 0,
            paid_by TEXT DEFAULT '',
            completed_by TEXT DEFAULT '',
            completion_note TEXT DEFAULT '',
            created_by TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS refills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_name TEXT NOT NULL,
            dosage TEXT NOT NULL,
            tablets_remaining INTEGER NOT NULL,
            daily_units INTEGER NOT NULL,
            source_prescription TEXT NOT NULL,
            claim_status TEXT NOT NULL DEFAULT 'unclaimed',
            claimed_by TEXT DEFAULT '',
            fulfillment_mode TEXT DEFAULT '',
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_name TEXT NOT NULL,
            actor_role TEXT NOT NULL,
            action TEXT NOT NULL,
            target_type TEXT NOT NULL,
            summary TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )

    # Migrations for existing databases to ensure columns exist
    for col, ctype in [("paid_by", "TEXT DEFAULT ''"), ("completed_by", "TEXT DEFAULT ''")]:
        try:
            cur.execute(f"ALTER TABLE tasks ADD COLUMN {col} {ctype}")
        except sqlite3.OperationalError:
            pass

    cur.execute("SELECT COUNT(*) FROM timeline_events")
    if cur.fetchone()[0] == 0:
        now = datetime.now()
        d_today = now.strftime("%Y-%m-%d")
        d_tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        d_minus2 = (now - timedelta(days=2)).strftime("%Y-%m-%d")
        d_minus5 = (now - timedelta(days=5)).strftime("%Y-%m-%d")

        events = [
            (
                "prescription",
                "Cardiology Follow-Up Prescription",
                d_minus2,
                "Source: Dr. R. K. Verma Prescription (Synthetic)",
                "Amlodipine 5mg (1 tab morning), Metformin 500mg (1 tab after dinner). Next review in 30 days.",
                "Priya Sharma",
                "family",
                (now - timedelta(days=2)).isoformat(timespec="minutes"),
            ),
            (
                "lab_report",
                "Fasting Blood Sugar & Lipid Panel",
                d_minus5,
                "Source: Apex Diagnostics Bhopal PDF (Synthetic)",
                "Lab report uploaded and filed for Dr. Verma's upcoming review. Organised for reference only.",
                "Arjun Sharma",
                "family",
                (now - timedelta(days=5)).isoformat(timespec="minutes"),
            ),
            (
                "appointment",
                "Dr. R. K. Verma — Cardiology Checkup",
                d_tomorrow,
                "Source: Clinic SMS Confirmation (Synthetic)",
                "10:30 AM at Bhopal Heart Care Clinic. Bring Nov lab report and current medicine strip.",
                "Priya Sharma",
                "family",
                (now - timedelta(hours=6)).isoformat(timespec="minutes"),
            ),
        ]
        cur.executemany(
            """
            INSERT INTO timeline_events
            (event_type, title, event_date, provider_or_source, details, created_by, visibility, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            events,
        )

        tasks = [
            (
                "Give 2:00 PM Calcium + Vitamin D3",
                "medication",
                "Sunita Devi",
                "attendant",
                d_today,
                "pending",
                0,
                0,
                "",
                "",
                "",
                "Priya Sharma",
                (now - timedelta(hours=3)).isoformat(timespec="minutes"),
            ),
            (
                "Escort Papa to Bhopal Heart Care (10:30 AM)",
                "appointment",
                "Priya Sharma",
                "primary",
                d_tomorrow,
                "pending",
                1,
                0,
                "",
                "",
                "Work meeting conflict — requesting sibling backup or cab coordination",
                "Priya Sharma",
                (now - timedelta(hours=2)).isoformat(timespec="minutes"),
            ),
            (
                "Order 30-day Metformin 500mg Strip Online",
                "refill",
                "Arjun Sharma",
                "remote",
                d_today,
                "completed",
                0,
                840,
                "Arjun Sharma",
                "Arjun Sharma",
                "Ordered via 1mg; delivery scheduled tomorrow 4 PM",
                "Arjun Sharma",
                (now - timedelta(hours=4)).isoformat(timespec="minutes"),
            ),
            (
                "Collect Fasting Blood Sugar Report",
                "lab",
                "Priya Sharma",
                "primary",
                d_minus5,
                "completed",
                0,
                1450,
                "Priya Sharma",
                "Priya Sharma",
                "Paid at Apex Diagnostics and uploaded PDF",
                "Priya Sharma",
                (now - timedelta(days=5)).isoformat(timespec="minutes"),
            ),
            (
                "Evening 6:00 PM BP Reading Log",
                "check",
                "Sunita Devi",
                "attendant",
                d_today,
                "completed",
                0,
                0,
                "",
                "Sunita Devi",
                "Logged reading in notebook",
                "Priya Sharma",
                (now - timedelta(hours=1)).isoformat(timespec="minutes"),
            ),
        ]
        cur.executemany(
            """
            INSERT INTO tasks
            (title, category, assigned_to, assigned_role, due_date, status, needs_backup, expense_inr, paid_by, completed_by, completion_note, created_by, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tasks,
        )

        refills = [
            (
                "Amlodipine 5mg",
                "1 tablet daily (Morning)",
                3,
                1,
                "Dr. Verma Rx (Nov)",
                "unclaimed",
                "",
                "",
                (now - timedelta(hours=5)).isoformat(timespec="minutes"),
            ),
            (
                "Metformin 500mg",
                "1 tablet daily (After Dinner)",
                4,
                1,
                "Dr. Verma Rx (Nov)",
                "ordered",
                "Arjun Sharma",
                "Online Delivery (Bengaluru -> Bhopal)",
                (now - timedelta(hours=4)).isoformat(timespec="minutes"),
            ),
            (
                "Atorvastatin 10mg",
                "1 tablet daily (Bedtime)",
                18,
                1,
                "Dr. Verma Rx (Oct)",
                "stocked",
                "Priya Sharma",
                "Local Pharmacy",
                (now - timedelta(days=2)).isoformat(timespec="minutes"),
            ),
        ]
        cur.executemany(
            """
            INSERT INTO refills
            (medicine_name, dosage, tablets_remaining, daily_units, source_prescription, claim_status, claimed_by, fulfillment_mode, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            refills,
        )

        logs = [
            (
                "Arjun Sharma",
                "remote",
                "REFILL_ORDERED",
                "refill",
                "Claimed & ordered Metformin 500mg online (₹840)",
                (now - timedelta(hours=4)).isoformat(timespec="minutes"),
            ),
            (
                "Priya Sharma",
                "primary",
                "BACKUP_REQUESTED",
                "task",
                "Flagged 'Escort Papa to Bhopal Heart Care' as Needs Backup",
                (now - timedelta(hours=2)).isoformat(timespec="minutes"),
            ),
            (
                "Sunita Devi",
                "attendant",
                "TASK_COMPLETED",
                "task",
                "Completed 'Evening 6:00 PM BP Reading Log'",
                (now - timedelta(hours=1)).isoformat(timespec="minutes"),
            ),
        ]
        cur.executemany(
            """
            INSERT INTO audit_logs
            (actor_name, actor_role, action, target_type, summary, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            logs,
        )

    conn.commit()
    conn.close()


def log_audit(conn, role_id, action, target_type, summary):
    role_info = ROLES.get(role_id, ROLES["remote"])
    conn.execute(
        """
        INSERT INTO audit_logs (actor_name, actor_role, action, target_type, summary, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            role_info["name"],
            role_id,
            action,
            target_type,
            summary,
            datetime.now().isoformat(timespec="minutes"),
        ),
    )


def has_perm(role_id, perm):
    return perm in ROLES.get(role_id, {}).get("permissions", [])


def extract_structured_note(text):
    """
    Extraction-only parser (no medical diagnosis or clinical advice).
    Turns a caregiver's plain-language note or OCR snippet into structured
    CareRelay timeline/task/refill drafts requiring human confirmation.
    """
    lowered = text.lower()
    for term in DIAGNOSTIC_BLOCKLIST:
        if re.search(r"\b" + re.escape(term) + r"\b", lowered) or term in lowered:
            return {
                "blocked": True,
                "reason": (
                    f"Guardrail triggered: detected clinical/diagnostic phrase ('{term}'). "
                    "CareRelay organizes logistics and records only—clinical decisions stay with doctors."
                ),
            }

    # Extract time / date hints
    today_str = datetime.now().strftime("%Y-%m-%d")
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    event_date = tomorrow_str if "tomorrow" in lowered else today_str

    # Heuristic type detection: Refill
    if any(w in lowered for w in ["refill", "strip", "tablets", "pharmacy", "medicine", "mg", "capsule", "syrup"]):
        med_match = re.search(r"([A-Za-z]+\s+\d+\s*(?:mg|ml|mcg)?)", text, re.IGNORECASE)
        med_name = med_match.group(1).strip() if med_match else "Prescription Refill"
        qty_match = re.search(r"(\d+)\s*(?:tab|tablets|days|strips|left|remaining)", lowered)
        qty = int(qty_match.group(1)) if qty_match else 5
        return {
            "blocked": False,
            "extracted": {
                "kind": "refill",
                "title": med_name,
                "dosage": "As per uploaded prescription",
                "tablets_remaining": qty,
                "daily_units": 1,
                "source_prescription": "Caregiver Note / Prescription Snippet (Verified)",
                "event_date": event_date,
            },
        }

    # Heuristic type detection: Appointment / Clinical visit
    if any(w in lowered for w in ["dr.", "dr ", "doctor", "appointment", "clinic", "hospital", "visit", "checkup", "cardio", "neuro"]):
        return {
            "blocked": False,
            "extracted": {
                "kind": "appointment",
                "title": text.strip()[:80],
                "event_date": event_date,
                "provider_or_source": "Caregiver Log / Clinic Communication (Verified)",
                "details": text.strip(),
            },
        }

    # Fallback: Task
    return {
        "blocked": False,
        "extracted": {
            "kind": "task",
            "title": text.strip()[:80],
            "category": "care",
            "assigned_to": "Priya Sharma",
            "assigned_role": "primary",
            "due_date": event_date,
        },
    }


class CareRelayHandler(BaseHTTPRequestHandler):
    def _send_json(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Care-Role")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length == 0:
                return {}
            raw = self.rfile.read(length).decode("utf-8")
            return json.loads(raw)
        except Exception:
            return {}

    def _get_role(self):
        role = self.headers.get("X-Care-Role", "remote").strip().lower()
        return role if role in ROLES else "remote"

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Care-Role")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path

            if path == "/api/dashboard":
                role_id = self._get_role()
                role_info = ROLES[role_id]
                conn = get_db()

                # Role-filtered timeline
                timeline = []
                if has_perm(role_id, "view_timeline"):
                    rows = conn.execute(
                        "SELECT * FROM timeline_events ORDER BY event_date DESC, id DESC"
                    ).fetchall()
                    timeline = [dict(r) for r in rows]

                # Role-filtered tasks
                # Order by pending tasks FIRST, then needs_backup, then due_date
                tasks = []
                if has_perm(role_id, "view_tasks"):
                    if role_id == "attendant":
                        rows = conn.execute(
                            """
                            SELECT id, title, category, assigned_to, assigned_role, due_date, status,
                                   needs_backup, completion_note, updated_at
                            FROM tasks
                            WHERE assigned_role = 'attendant'
                            ORDER BY CASE WHEN status = 'pending' THEN 0 ELSE 1 END,
                                     needs_backup DESC, due_date ASC
                            """
                        ).fetchall()
                    else:
                        rows = conn.execute(
                            """
                            SELECT * FROM tasks
                            ORDER BY CASE WHEN status = 'pending' THEN 0 ELSE 1 END,
                                     needs_backup DESC, due_date ASC
                            """
                        ).fetchall()
                    tasks = [dict(r) for r in rows]

                # Refills: sorted by runway (days_left ASC)
                refills = []
                if has_perm(role_id, "view_refills"):
                    rows = conn.execute("SELECT * FROM refills").fetchall()
                    for r in rows:
                        item = dict(r)
                        daily = max(1, item.get("daily_units", 1))
                        item["days_left"] = round(item["tablets_remaining"] / daily, 1)
                        refills.append(item)
                    refills.sort(key=lambda x: (x["days_left"], x["medicine_name"]))

                # Audit logs (latest 30)
                audit_logs = []
                if has_perm(role_id, "view_audit"):
                    rows = conn.execute(
                        "SELECT * FROM audit_logs ORDER BY id DESC LIMIT 30"
                    ).fetchall()
                    audit_logs = [dict(r) for r in rows]

                # Fairness & Care-load metrics (family siblings)
                fairness = []
                if has_perm(role_id, "view_fairness"):
                    # Pre-populate both primary family siblings so balance is always visible
                    metrics_map = {
                        "Priya Sharma": {"member": "Priya Sharma (Local)", "tasks_done": 0, "tasks_pending": 0, "total_inr": 0.0},
                        "Arjun Sharma": {"member": "Arjun Sharma (Remote)", "tasks_done": 0, "tasks_pending": 0, "total_inr": 0.0},
                    }

                    all_tasks = conn.execute("SELECT * FROM tasks").fetchall()
                    for t in all_tasks:
                        assignee = t["assigned_to"]
                        key = "Priya Sharma" if "Priya" in assignee else ("Arjun Sharma" if "Arjun" in assignee else None)
                        if key:
                            if t["status"] == "completed":
                                metrics_map[key]["tasks_done"] += 1
                            else:
                                metrics_map[key]["tasks_pending"] += 1

                        # Credit expense to the member who actually paid
                        payer = t["paid_by"] or t["assigned_to"]
                        payer_key = "Priya Sharma" if "Priya" in payer else ("Arjun Sharma" if "Arjun" in payer else None)
                        if payer_key and t["expense_inr"] > 0:
                            metrics_map[payer_key]["total_inr"] += float(t["expense_inr"])

                    fairness = list(metrics_map.values())

                conn.close()
                self._send_json(
                    200,
                    {
                        "patient": {
                            "name": "Ramesh Sharma (Synthetic Profile)",
                            "age": 72,
                            "city": "Bhopal, MP",
                            "guardrail": "Organizes information only. Does not diagnose or give medical advice.",
                        },
                        "role": role_info,
                        "all_roles": list(ROLES.values()),
                        "timeline": timeline,
                        "tasks": tasks,
                        "refills": refills,
                        "audit_logs": audit_logs,
                        "fairness": fairness,
                    },
                )
                return

            # Serve static files
            if path == "/" or path == "":
                path = "/index.html"
            safe_path = os.path.normpath(path.lstrip("/"))
            file_path = os.path.join(STATIC_DIR, safe_path)
            if not file_path.startswith(STATIC_DIR) or not os.path.isfile(file_path):
                self.send_error(404, "File not found")
                return

            ctype, _ = mimetypes.guess_type(file_path)
            with open(file_path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", ctype or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self._send_json(500, {"error": f"Internal server error: {str(e)}"})

    def do_POST(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            role_id = self._get_role()
            data = self._read_json()

            if path == "/api/extract":
                if not has_perm(role_id, "ingest_records"):
                    self._send_json(403, {"error": "Your role cannot ingest new records."})
                    return
                text = data.get("text", "").strip()
                if not text:
                    self._send_json(400, {"error": "Please enter a note or prescription snippet."})
                    return
                self._send_json(200, extract_structured_note(text))
                return

            conn = get_db()
            try:
                # 1. Manual / Confirmed Timeline Record
                if path == "/api/timeline":
                    if not has_perm(role_id, "ingest_records"):
                        self._send_json(403, {"error": "Forbidden for current role."})
                        return

                    title = data.get("title", "").strip()
                    if not title:
                        self._send_json(400, {"error": "Title is required for timeline event."})
                        return

                    event_date = data.get("event_date", datetime.now().strftime("%Y-%m-%d"))
                    event_type = data.get("event_type", "appointment")
                    provider = data.get("provider_or_source", "Caregiver Log (Verified)")
                    details = data.get("details", "")

                    conn.execute(
                        """
                        INSERT INTO timeline_events
                        (event_type, title, event_date, provider_or_source, details, created_by, visibility, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'family', ?)
                        """,
                        (
                            event_type,
                            title,
                            event_date,
                            provider,
                            details,
                            ROLES[role_id]["name"],
                            datetime.now().isoformat(timespec="minutes"),
                        ),
                    )
                    log_audit(conn, role_id, "RECORD_ADDED", "timeline", f"Added '{title}' ({event_type})")

                    # If requested, automatically create companion escort/reminder task
                    if data.get("create_companion_task"):
                        assigned_to = data.get("assigned_to", "Priya Sharma")
                        assigned_role = "attendant" if "Sunita" in assigned_to else ("remote" if "Arjun" in assigned_to else "primary")
                        conn.execute(
                            """
                            INSERT INTO tasks
                            (title, category, assigned_to, assigned_role, due_date, status, needs_backup, expense_inr, completion_note, created_by, updated_at)
                            VALUES (?, 'appointment', ?, ?, ?, 'pending', 0, 0, '', ?, ?)
                            """,
                            (
                                f"Escort / Coordinate: {title}",
                                assigned_to,
                                assigned_role,
                                event_date,
                                ROLES[role_id]["name"],
                                datetime.now().isoformat(timespec="minutes"),
                            ),
                        )
                        log_audit(conn, role_id, "TASK_CREATED", "task", f"Created escort task for '{title}'")

                    conn.commit()
                    self._send_json(201, {"ok": True})
                    return

                # 2. Manual / Confirmed Task Creation
                if path == "/api/tasks":
                    if not has_perm(role_id, "manage_tasks"):
                        self._send_json(403, {"error": "Forbidden for current role."})
                        return

                    title = data.get("title", "").strip()
                    if not title:
                        self._send_json(400, {"error": "Task title is required."})
                        return

                    assigned_to = data.get("assigned_to", "Priya Sharma")
                    assigned_role = "attendant" if "Sunita" in assigned_to else ("remote" if "Arjun" in assigned_to else "primary")
                    due_date = data.get("due_date", datetime.now().strftime("%Y-%m-%d"))
                    category = data.get("category", "care")

                    conn.execute(
                        """
                        INSERT INTO tasks
                        (title, category, assigned_to, assigned_role, due_date, status, needs_backup, expense_inr, paid_by, completed_by, completion_note, created_by, updated_at)
                        VALUES (?, ?, ?, ?, ?, 'pending', 0, 0, '', '', '', ?, ?)
                        """,
                        (
                            title,
                            category,
                            assigned_to,
                            assigned_role,
                            due_date,
                            ROLES[role_id]["name"],
                            datetime.now().isoformat(timespec="minutes"),
                        ),
                    )
                    log_audit(conn, role_id, "TASK_CREATED", "task", f"Assigned '{title}' to {assigned_to}")
                    conn.commit()
                    self._send_json(201, {"ok": True})
                    return

                # 3. Task Actions: Complete, Backup, Cancel Backup, Claim
                if path.startswith("/api/tasks/") and path.endswith("/action"):
                    parts = path.split("/")
                    if len(parts) < 5 or not parts[3].isdigit():
                        self._send_json(400, {"error": "Invalid task ID"})
                        return

                    task_id = int(parts[3])
                    action = data.get("action")
                    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
                    if not task:
                        self._send_json(404, {"error": "Task not found"})
                        return

                    actor_name = ROLES[role_id]["name"]
                    now_str = datetime.now().isoformat(timespec="minutes")

                    if action == "complete":
                        if role_id == "attendant" and task["assigned_role"] != "attendant":
                            self._send_json(403, {"error": "Attendants can only complete their own tasks."})
                            return
                        if not (has_perm(role_id, "manage_tasks") or has_perm(role_id, "complete_assigned_tasks")):
                            self._send_json(403, {"error": "Forbidden for current role."})
                            return

                        raw_expense = data.get("expense_inr", 0)
                        try:
                            expense = max(0.0, float(raw_expense)) if role_id != "attendant" else 0.0
                        except (ValueError, TypeError):
                            expense = 0.0

                        note = str(data.get("note", "Completed")).strip() or "Completed"
                        paid_by = actor_name if expense > 0 else ""

                        conn.execute(
                            """
                            UPDATE tasks
                            SET status = 'completed', needs_backup = 0, expense_inr = ?,
                                paid_by = ?, completed_by = ?, completion_note = ?, updated_at = ?
                            WHERE id = ?
                            """,
                            (expense, paid_by, actor_name, note, now_str, task_id),
                        )
                        summary = f"Completed '{task['title']}'" + (f" (₹{int(expense)})" if expense > 0 else "")
                        log_audit(conn, role_id, "TASK_COMPLETED", "task", summary)

                    elif action == "backup":
                        if not has_perm(role_id, "manage_tasks"):
                            self._send_json(403, {"error": "Forbidden for current role."})
                            return
                        conn.execute(
                            "UPDATE tasks SET needs_backup = 1, updated_at = ? WHERE id = ?",
                            (now_str, task_id),
                        )
                        log_audit(conn, role_id, "BACKUP_REQUESTED", "task", f"Requested sibling backup for '{task['title']}'")

                    elif action == "cancel_backup":
                        if not has_perm(role_id, "manage_tasks"):
                            self._send_json(403, {"error": "Forbidden for current role."})
                            return
                        conn.execute(
                            "UPDATE tasks SET needs_backup = 0, updated_at = ? WHERE id = ?",
                            (now_str, task_id),
                        )
                        log_audit(conn, role_id, "BACKUP_CANCELLED", "task", f"Cleared backup request for '{task['title']}'")

                    elif action == "claim":
                        if not has_perm(role_id, "manage_tasks"):
                            self._send_json(403, {"error": "Forbidden for current role."})
                            return
                        conn.execute(
                            "UPDATE tasks SET assigned_to = ?, assigned_role = ?, needs_backup = 0, updated_at = ? WHERE id = ?",
                            (actor_name, role_id, now_str, task_id),
                        )
                        log_audit(conn, role_id, "TASK_CLAIMED", "task", f"Claimed '{task['title']}'")
                    else:
                        self._send_json(400, {"error": f"Unknown action '{action}'"})
                        return

                    conn.commit()
                    self._send_json(200, {"ok": True})
                    return

                # 4. Manual Refill Addition
                if path == "/api/refills":
                    if not has_perm(role_id, "manage_refills"):
                        self._send_json(403, {"error": "Forbidden for current role."})
                        return

                    med_name = data.get("medicine_name", "").strip()
                    if not med_name:
                        self._send_json(400, {"error": "Medicine name is required."})
                        return

                    dosage = data.get("dosage", "1 tablet daily").strip() or "1 tablet daily"
                    try:
                        tablets = max(0, int(data.get("tablets_remaining", 5)))
                    except (ValueError, TypeError):
                        tablets = 5

                    try:
                        daily = max(1, int(data.get("daily_units", 1)))
                    except (ValueError, TypeError):
                        daily = 1

                    source = data.get("source_prescription", "Caregiver Entry (Verified)").strip()
                    now_str = datetime.now().isoformat(timespec="minutes")

                    conn.execute(
                        """
                        INSERT INTO refills
                        (medicine_name, dosage, tablets_remaining, daily_units, source_prescription, claim_status, claimed_by, fulfillment_mode, updated_at)
                        VALUES (?, ?, ?, ?, ?, 'unclaimed', '', '', ?)
                        """,
                        (med_name, dosage, tablets, daily, source, now_str),
                    )
                    log_audit(conn, role_id, "REFILL_ADDED", "refill", f"Added refill tracker for {med_name} ({tablets} tabs)")
                    conn.commit()
                    self._send_json(201, {"ok": True})
                    return

                # 5. Claim / Order Refill
                if path.startswith("/api/refills/") and path.endswith("/claim"):
                    if not has_perm(role_id, "manage_refills"):
                        self._send_json(403, {"error": "Forbidden for current role."})
                        return

                    parts = path.split("/")
                    if len(parts) < 5 or not parts[3].isdigit():
                        self._send_json(400, {"error": "Invalid refill ID"})
                        return

                    refill_id = int(parts[3])
                    refill = conn.execute("SELECT * FROM refills WHERE id = ?", (refill_id,)).fetchone()
                    if not refill:
                        self._send_json(404, {"error": "Refill not found"})
                        return

                    mode = data.get("mode", "Online Order" if role_id == "remote" else "Local Pharmacy Pickup")
                    actor_name = ROLES[role_id]["name"]
                    now_str = datetime.now().isoformat(timespec="minutes")

                    conn.execute(
                        "UPDATE refills SET claim_status = 'ordered', claimed_by = ?, fulfillment_mode = ?, updated_at = ? WHERE id = ?",
                        (actor_name, mode, now_str, refill_id),
                    )
                    log_audit(conn, role_id, "REFILL_CLAIMED", "refill", f"Claimed {refill['medicine_name']} ({mode})")
                    conn.commit()
                    self._send_json(200, {"ok": True})
                    return

                # 6. Restock / Mark Refill Delivered
                if path.startswith("/api/refills/") and path.endswith("/restock"):
                    if not has_perm(role_id, "manage_refills"):
                        self._send_json(403, {"error": "Forbidden for current role."})
                        return

                    parts = path.split("/")
                    if len(parts) < 5 or not parts[3].isdigit():
                        self._send_json(400, {"error": "Invalid refill ID"})
                        return

                    refill_id = int(parts[3])
                    refill = conn.execute("SELECT * FROM refills WHERE id = ?", (refill_id,)).fetchone()
                    if not refill:
                        self._send_json(404, {"error": "Refill not found"})
                        return

                    try:
                        added = max(1, int(data.get("tablets_added", 30)))
                    except (ValueError, TypeError):
                        added = 30

                    new_total = refill["tablets_remaining"] + added
                    actor_name = ROLES[role_id]["name"]
                    now_str = datetime.now().isoformat(timespec="minutes")
                    today_str = datetime.now().strftime("%Y-%m-%d")

                    conn.execute(
                        "UPDATE refills SET tablets_remaining = ?, claim_status = 'stocked', updated_at = ? WHERE id = ?",
                        (new_total, now_str, refill_id),
                    )
                    log_audit(conn, role_id, "REFILL_RESTOCKED", "refill", f"Restocked {refill['medicine_name']} (+{added} tabs, total: {new_total})")

                    # Log to timeline
                    conn.execute(
                        """
                        INSERT INTO timeline_events
                        (event_type, title, event_date, provider_or_source, details, created_by, visibility, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'family', ?)
                        """,
                        (
                            "refill",
                            f"Refill Restocked: {refill['medicine_name']}",
                            today_str,
                            f"Verified by {actor_name}",
                            f"Added {added} tablets to current supply. Total remaining: {new_total}.",
                            actor_name,
                            now_str,
                        ),
                    )

                    conn.commit()
                    self._send_json(200, {"ok": True, "new_total": new_total})
                    return

                self._send_json(404, {"error": "Endpoint not found"})
            finally:
                conn.close()
        except Exception as e:
            self._send_json(500, {"error": f"Internal server error: {str(e)}"})


def main():
    init_db()
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), CareRelayHandler)
    print(f"CareRelay prototype running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()


if __name__ == "__main__":
    main()
