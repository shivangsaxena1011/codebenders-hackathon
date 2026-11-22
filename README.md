# CareRelay — The Family Care Hub (ACE Builders' Hackathon 2026 | PS 4)

A working, zero-dependency full-stack application for **Problem Statement 4: Health and Family Care (The Family Care Hub)**. Built with **Python 3 + SQLite3** on the backend and a **responsive PWA** on the frontend.

---

## Quick Start (Laptop or Android Termux)

1. Open the prototype directory:
   ```bash
   cd carerelay_prototype
   ```
2. Start the server (uses Python 3 standard library only — no `pip install` required):
   ```bash
   python3 server.py
   ```
3. Open **http://localhost:8080** in your browser.

---

## Key Features & Problem Statement 4 Alignment

- **10-Second Remote Briefing ("Pulse View")**: Specifically built for a sibling living 2,000 km away (Arjun in Bengaluru) to instantly know:
  1. *Needs Action Now* (Urgent refills under 5 days, tasks needing sibling backup)
  2. *Who Is On Point Today* (Active pending assignees)
  3. *Latest Verified Update* (Live append-only audit trail snapshot)
- **4-Tier Server-Enforced RBAC**: Real backend and UI filtering switched live in the top bar:
  - **Primary Caregiver (Priya Sharma, Bhopal)**: Full operational control, task creation, record ingestion, expense logging.
  - **Remote Co-Manager (Arjun Sharma, Bengaluru)**: Full timeline, task claiming, online medicine ordering, and care fairness metrics.
  - **Care Attendant (Sunita Devi, Bhopal)**: *Task-Only view* — family expenses, medical history, and clinical records are completely stripped by the server.
  - **Doctor 24h Pass (Dr. R. K. Verma)**: Read-only factual timeline, active tracked medications, and printable Doctor Visit Brief.
- **Smart Note / Prescription Extractor (Non-Diagnostic Guardrail)**: Parses plain notes and clinic SMS into structured Appointments, Refills, or Tasks with a mandatory human confirmation step. Contains a strict blocklist blocking diagnostic statements or dosage alterations.
- **Split-City Refill Runway**: Automatically calculates days of medication left from tablet count and daily dose. Allows local pharmacy pickup (Bhopal) or remote online ordering (Bengaluru) with restock confirmation.
- **Care-Load & Expense Fairness Meter**: Balances physical care tasks and out-of-pocket ₹ expenditures between siblings across cities.
- **One-Tap Doctor Visit Brief**: Clean, printable summary modal (`Ctrl+P` / Print Brief) formatted specifically for physician consultations.
- **Immutable "Who Did What" Audit Ledger**: Every task claim, completion, backup request, refill order, and restock is permanently recorded in SQLite.
- **Offline Clinic Mode (PWA)**: Service worker caches the app shell and local storage caches the latest verified dashboard snapshot.

---

## Hackathon Submission & Codebenders Guidance

1. **Codebenders Mandatory Rule**: Re-run the development prompts in your Codebenders environment to ensure full prompt iteration history in your account.
2. **Deployment**: Deploy this zero-dependency server on any cloud host (Render, Fly.io, Railway, PythonAnywhere, or Codebenders hosting).
3. **Monetization Pitch (Who Pays?)**:
   - **B2C**: ₹299/month family subscription for multi-sibling expense fairness and automated doctor visit briefs.
   - **B2B Eldercare Benefit**: Subsidized employee benefit for IT companies addressing eldercare stress among remote workers.
   - **B2B2C**: White-labeled portal for home nursing and eldercare agencies.

> **Guardrail Notice:** Uses 100% synthetic demo data (*Ramesh Sharma, 72, Bhopal*). Organizes logistics and records only; does not diagnose or provide medical advice.
