# CareRelay — The Family Care Hub
### ACE Builders' Hackathon 2026 | Problem Statement 4: Health and Family Care

[![Hackathon](https://img.shields.io/badge/Hackathon-Codebenders_ACE_Builders_2026-0f766e?style=for-the-badge)](https://app.codebenders.ai/hackathon)
[![Problem Statement](https://img.shields.io/badge/Problem_Statement_4-Health_%26_Family_Care-blue?style=for-the-badge)](https://app.codebenders.ai/hackathon)
[![Stack](https://img.shields.io/badge/Stack-Python_3_%2B_SQLite3_%2B_Vanilla_PWA-15803d?style=for-the-badge)](#technical-architecture--zero-dependency-stack)
[![Mobile Optimized](https://img.shields.io/badge/Mobile-100%25_Responsive_(0px_Overflow)-purple?style=for-the-badge)](#mobile-optimization--pwa-resilience)
[![Clinical Guardrails](https://img.shields.io/badge/Guardrails-Non--Diagnostic_Enforced-b91c1c?style=for-the-badge)](#clinical-safety--non-diagnostic-guardrails)

---

## Executive Summary

When an aging parent or grandparent requires continuous medical care, logistics rapidly fragment across disparate messaging apps, paper prescriptions, lab PDFs, and clinic appointments. Adult siblings—often living thousands of kilometers apart—struggle with asymmetric workloads, missed refills, unclear responsibilities, and emotional friction.

**CareRelay** is a unified, mobile-first coordination hub built specifically for long-distance families. It synchronizes medical records, coordinates tasks, monitors prescription runways, balances caregiving expenses across siblings, and enforces strict non-diagnostic clinical boundaries.

---

## 🏆 ACE Builders' Hackathon 2026 — Official Overview

CareRelay was engineered for the **ACE Builders' Hackathon 2026**, organized globally by **Codebenders**.

| Detail | Official Hackathon Information |
| :--- | :--- |
| **Organizer** | **Codebenders** ([app.codebenders.ai/hackathon](https://app.codebenders.ai/hackathon)) |
| **Theme** | *Build. Get Discovered. Belong. Keep Building.* |
| **Dates** | **November 21 & 22, 2026** (Global Online, Solo or Duo) |
| **Total Prize Pool** | **₹2,00,000** + Talent Pool Job Opportunities + AI Tokens + Mentorship |
| **Development Platform** | **Codebenders IDE** (Mandatory Development Tool) |
| **Official Support** | `ai@codebenders.ai` • WhatsApp Community • +91 9247527050 |

### Post-Hackathon Evaluation Timeline

```
Nov 21 - 22, 2026       Nov 23 - 24, 2026       Nov 25 - Dec 3, 2026      Dec 4, 2026          Dec 5, 2026
┌────────────────┐     ┌────────────────┐     ┌─────────────────────┐    ┌─────────────────┐  ┌──────────────────┐
│ Hackathon Build│ ──> │ Project Final  │ ──> │ Jury Evaluation &   │ ──>│ Winner Identity │─>│ Official Winners │
│ Period (Ends   │     │ Submission     │     │ Project Judging     │    │ Verification    │  │ Announcement     │
│ 11:59 PM Sun)  │     │ Window (2 Days)│     │ Window              │    │                 │  │                  │
└────────────────┘     └────────────────┘     └─────────────────────┘    └─────────────────┘  └──────────────────┘
```

### Official Evaluation Criteria & Weightage

All hackathon submissions are judged against five weighted pillars:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Working Product (30%)                                                    │
│    Fully functional, zero-dependency deployed application with live state.  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. Business Viability (25%)                                                 │
│    Clear path to monetization (B2C eldercare freemium + B2B employee perk). │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. Problem and User Clarity (20%)                                           │
│    Empathy-driven workflow tailored for remote & local siblings in India.   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. Build Quality and Use of Codebenders (15%)                               │
│    Modular, clean code architecture built iteratively using Codebenders.    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5. Presentation (10%)                                                       │
│    Live 4-tier RBAC switcher, Doctor Visit Brief, and concise UI story.     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Problem Statement 4: Health and Family Care

### The Family Care Hub

* **The Problem**: When a parent or grandparent needs ongoing care, the work is scattered across siblings, medical reports, prescriptions, and appointments. Things get missed, and caregivers in different cities are never on the same page.
* **Who It Is For**: Adult children, often living in different cities, who coordinate care for an elderly or chronically ill relative.
* **The Challenge**: Build a shared coordination product for the family that keeps records, schedules, tasks, and updates in one place and makes it clear who is doing what.

### Mandatory Requirements Matrix

| Problem Statement Requirement | CareRelay Implementation |
| :--- | :--- |
| **Shared records & timeline** | Unified chronological timeline tracking clinic appointments, multi-drug prescriptions, and diagnostic lab reports with verified source attribution. |
| **Task assignment & reminders** | Dynamic task allocation with due dates, categorized tags, and an active *"Needs Sibling Backup"* handoff mechanism. |
| **Refill & appointment tracker** | Algorithmic **Smart Refill Runway** auto-calculating supply days left (`tablets / daily_dose`) with local vs. remote order claiming and restock confirmation. |
| **Role-based access control (RBAC)** | 4-tier server-enforced RBAC: Primary Local Caregiver, Remote Co-Manager, Task-Only Care Attendant, and 24h Read-Only Doctor Pass. |
| **"Who did what & what is pending"** | Append-only immutable SQLite audit ledger logging every action, coupled with pending-first task priority views. |
| **Non-Diagnostic Guardrails** | Extraction-only parser equipped with regex-based clinical keyword blocklists, mandatory human confirmation, and strict non-diagnostic banners. |

### The Three Guiding Questions (Addressed Directly)

#### 1. What does a sibling 2,000 km away need to see in ten seconds?
CareRelay answers this through the **"Pulse View"** pinned to the top of the dashboard:
* **Box 1 (Needs Action Now)**: Quantifies urgent medication shortages (<5 days left) and unresolved sibling backup requests.
* **Box 2 (Who Is On Point Today)**: Identifies exactly which caregiver owns today’s active clinical schedule.
* **Box 3 (Latest Verified Update)**: Pulls the most recent verified event directly from the immutable audit ledger.

#### 2. How do you handle sensitive health information responsibly?
* **Server-Enforced Data Stripping**: Sensitive medical records, diagnostic histories, and financial out-of-pocket metrics are strictly filtered at the backend HTTP layer—never merely hidden via CSS.
* **Privacy Sandboxing**: External attendants see only routine physical tasks (e.g., *"Administer 2:00 PM Calcium"*); they cannot view family financial splits or clinical diagnoses.
* **Time-Bound Physician Links**: Doctors receive read-only consultation passes that expire, granting access solely to current medications and chronological clinic visits.

#### 3. Who would pay: the family, a care agency, or an employer benefit programme?
CareRelay implements a three-pronged business model:
1. **B2C Family Subscription (₹299/month)**: Free shared tasks; premium tier unlocks automated document parsing, unlimited Doctor Visit Brief exports, and multi-sibling expense fairness settlement.
2. **B2B Corporate Wellness Benefit**: Subsidized eldercare benefit sponsored by IT and MNC employers in metro hubs (Bengaluru, Gurgaon, Hyderabad) to reduce absenteeism among mid-to-senior engineers managing elderly parents in tier-2 cities.
3. **B2B2C Eldercare Agency White-Label**: Licensed to home-nursing agencies (e.g., Portea, Apollo HomeCare) to offer families transparent proof-of-care portals.

---

## 💡 CareRelay: Solution Architecture & Deep Walkthrough

```
                                  ┌───────────────────────────────┐
                                  │      CareRelay Web / PWA      │
                                  │   (Responsive • Offline SW)   │
                                  └──────────────┬────────────────┘
                                                 │ HTTP / REST
                                                 ▼
               ┌──────────────────────────────────────────────────────────────────┐
               │              Python 3 Standard Library HTTP Engine               │
               │            (ThreadingHTTPServer • 0 External Dependencies)        │
               └─────────┬───────────────────────┬──────────────────────┬─────────┘
                         │                       │                      │
                         ▼                       ▼                      ▼
               ┌───────────────────┐   ┌───────────────────┐  ┌───────────────────┐
               │    4-Tier RBAC    │   │  Smart Extractor  │  │   Runway Engine   │
               │ Permission Engine │   │ Non-Diagnostic OK │  │ (tablets / dose)  │
               └─────────┬─────────┘   └─────────┬─────────┘  └─────────┬─────────┘
                         │                       │                      │
                         └───────────────────────┼──────────────────────┘
                                                 ▼
                               ┌──────────────────────────────────┐
                               │     SQLite3 Relational Store     │
                               │  Timeline • Tasks • Refills •    │
                               │      Immutable Audit Logs        │
                               └──────────────────────────────────┘
```

### Core Product Capabilities

#### 1. 10-Second Remote Briefing ("Pulse View")
Arjun in Bengaluru opens the app between morning meetings. Within 3 seconds, he sees:
* **Needs Action Now**: `1 Action Needed` — *Amlodipine 5mg (3.0d left)*.
* **Who Is On Point Today**: *Priya Sharma (Local)* escorting Papa to Bhopal Heart Care.
* **Latest Verified Update**: *Dr. Verma follow-up confirmed*.

#### 2. 4-Tier Server-Enforced RBAC
Users can switch roles dynamically in the top navigation bar to test live backend permission enforcement:

```
┌─────────────────────────────────┬───────────┬──────────┬─────────────┬──────────────┬───────────────┐
│ Role Persona                    │ Pulse View│ Tasks    │ Refill Hub  │ Full Timeline│ Expense / Fair│
├─────────────────────────────────┼───────────┼──────────┼─────────────┼──────────────┼───────────────┤
│ Priya (Primary Caregiver Bhopal)│ Full View │ Manage   │ Manage      │ Full Read/Add│ Full Read/Edit│
│ Arjun (Remote Co-Manager Blr)   │ Full View │ Manage   │ Order Claim │ Full Read/Add│ Full Read/Edit│
│ Sunita Devi (Care Attendant)    │ Hidden    │ Assigned │ Hidden      │ Hidden       │ Stripped (₹0) │
│ Dr. R. K. Verma (Physician)     │ Hidden    │ Hidden   │ Read-Only   │ Clinical Only│ Hidden        │
└─────────────────────────────────┴───────────┴──────────┴─────────────┴──────────────┴───────────────┘
```

#### 3. Smart Note / Prescription Extractor (Non-Diagnostic Guardrail)
Family members frequently paste rushed clinic SMS messages, WhatsApp notes, or raw prescription lines. The integrated extraction parser categorizes unstructured text into structured drafts:
* Automatically detects medicines, dosages, quantities, and dates.
* **Human Confirmation Gate**: Parsed items are never auto-committed; a caregiver must review and click *"Confirm & Save to Hub"*.
* If an appointment is extracted, a checkbox option allows one-click generation of a companion sibling escort task.

#### 4. Split-City Refill Runway
Medication non-adherence is the leading cause of hospital readmission among seniors. CareRelay calculates runway dynamically:
$$\text{Runway (Days Left)} = \frac{\text{Tablets Remaining}}{\text{Daily Dose}}$$
* Medications are sorted strictly by `days_left ASC`, ensuring critically low supplies appear at the top.
* **Remote Ordering**: Arjun in Bengaluru clicks *"Claim Refill"* to order via online delivery platforms (1mg, Apollo) directly to Bhopal.
* **Restock Confirmation**: When the package arrives, Priya in Bhopal clicks *"Mark Delivered (+30 tabs)"* to replenish the runway, logging the event in both the audit ledger and shared timeline.

#### 5. Care-Load & Expense Fairness Meter
Caregiving often leads to silent resentment between local and remote siblings. CareRelay tracks:
* **Physical Effort**: Number of completed routine, clinic escort, and lab pickup tasks.
* **Financial Equality**: Out-of-pocket ₹ expenditures credited accurately to the sibling who paid.
* Transparent metrics eliminate financial friction and maintain family harmony.

#### 6. One-Tap Printable Doctor Visit Brief
During brief 10-minute clinic consultations, elderly parents and caregivers often forget recent dosage changes or prior lab results.
* Clicking **"Doctor Visit Brief"** generates a clean, printable consultation summary (`Ctrl+P` / Save PDF).
* Formatted strictly without UI clutter, buttons, or navigation bars.

#### 7. Immutable "Who Did What" Audit Ledger
Every operational change is appended to the `audit_logs` table:
* *Actor, Role, Action Type, Target Entity, Summary, Timestamp*.
* Ensures zero ambiguity over whether a task was completed or medicine was ordered.

---

## 🔒 Clinical Safety & Non-Diagnostic Guardrails

Problem Statement 4 establishes strict guardrails:
> *"The product organises information only. It must not diagnose or give medical advice, and clinical decisions stay with doctors. Use sample or synthetic data only, never real patient records."*

CareRelay enforces this programmatically:
1. **Diagnostic Keyword Blocklist**: An active filter rejects diagnostic assertions, dosage alteration instructions, or clinical claims:
   ```python
   DIAGNOSTIC_BLOCKLIST = [
       "diagnose", "diagnosis", "stop taking", "increase dose",
       "decrease dose", "double dose", "cancer", "heart attack", "stroke risk",
       "you should take", "recommended treatment"
   ]
   ```
   * *Legitimate prescription logging* (`"Dr. Verma prescribed Metformin 500mg"`) is supported.
   * *Diagnostic inputs* (`"You should double dose and diagnose high BP"`) are actively blocked with an educational warning.
2. **Synthetic Data Sandbox**: Pre-seeded demo dataset models a realistic Indian eldercare scenario:
   * **Patient**: Ramesh Sharma, 72, Bhopal, MP (Hypertension & Type-2 Diabetes).
   * **Local Caregiver**: Priya Sharma (Daughter, Bhopal).
   * **Remote Caregiver**: Arjun Sharma (Son, Senior Software Engineer, Bengaluru).
   * **Attendant**: Sunita Devi (Daily physical care attendant).
   * **Physician**: Dr. R. K. Verma (Cardiologist, Bhopal Heart Care).

---

## 📱 Mobile Optimization & PWA Resilience

Caregivers primarily use their smartphones while traveling, working, or sitting in clinic waiting rooms.

```
┌─────────────────────────────────┐
│ [CR] CareRelay                  │
│ Ramesh Sharma • Age 72 • Bhopal │
├─────────────────────────────────┤
│ Active Role:                    │
│ [ Arjun Sharma (Remote)       ▼]│
│ [   Doctor Visit Brief        ] │
├─────────────────────────────────┤
│ 1. NEEDS ACTION NOW             │
│ 1 Action Needed                 │
│ Amlodipine 5mg (3.0d left)      │
├─────────────────────────────────┤
│ 2. WHO IS ON POINT TODAY        │
│ 1 Pending • Owner: Priya Sharma │
├─────────────────────────────────┤
│ 3. LATEST VERIFIED UPDATE       │
│ Arjun Sharma: Claimed Refill    │
├─────────────────────────────────┤
│ TASKS & HANDOFFS                │
│ Escort Papa to Bhopal Heart Care│
│ [Needs Sibling Backup]          │
│ [Mark Done] [Claim] [Cancel]    │
└─────────────────────────────────┘
```

* **0px Horizontal Overflow**: Tested and verified on modern mobile viewports (390x844). Content scales neatly with zero sideways scrolling.
* **Touch-Optimized Controls**: Minimum 36px–38px tap targets designed for quick operation.
* **iOS Zoom Prevention**: Form fields enforce `font-size: 16px` on mobile, preventing unwanted auto-zooming in iOS Safari.
* **Offline Clinic Cache**: Service Worker (`sw.js`) and `localStorage` cache the app shell and recent snapshots so caregivers can access records even in hospital basements with poor cellular reception.

---

## 🚀 Execution & Deployment Guide

CareRelay was intentionally engineered with **zero third-party dependencies**, running entirely on the standard Python 3 runtime and vanilla browser APIs.

### Running Locally

```bash
# 1. Navigate to the project directory
cd carerelay_prototype

# 2. Launch the server (uses Python 3 standard library only)
python server.py
```

Open **http://localhost:8080** in any desktop or mobile browser.

### Cloud Deployment (Render, Fly.io, Railway)

The repository includes a production-ready `Procfile` and standard HTTP port binding (`PORT` environment variable):

```
Procfile:
web: python server.py
```

* **Render / Railway**: Connect this GitHub repository, choose **Python Runtime**, and deploy.
* **No `pip install` required**: Starts in under 2 seconds.

---

## 📁 Repository Structure

```
codebenders-hackathon/
├── server.py              # Zero-dependency Python 3 HTTP engine, RBAC, SQLite layer & guardrails
├── Procfile               # Cloud deployment process file (Render / Railway)
├── requirements.txt       # Standard environment descriptor (zero external dependencies)
├── .gitignore             # Ignores temporary databases and bytecode caches
├── README.md              # Comprehensive project, hackathon, and problem statement documentation
└── static/                # Single-Page PWA Application
    ├── index.html         # Semantic HTML5 layout, accessible modals & forms
    ├── styles.css         # Modern responsive CSS design system (mobile-first, 0px overflow)
    ├── app.js             # Client state manager, RBAC filter, offline sync & API client
    ├── manifest.json      # Progressive Web App (PWA) installation manifest
    ├── sw.js              # Service Worker managing offline shell and snapshot caching
    └── icon.svg           # High-resolution vector brand mark for PWA homescreen install
```

---

## ⚖️ Code of Conduct & Declarations

* **Hackathon Integrity**: Developed in compliance with official ACE Builders' Hackathon 2026 rules.
* **Original Work**: Engineered from scratch for Problem Statement 4; no pre-packaged templates.
* **Synthetic Records**: 100% synthetic medical data; no real patient health information (PHI) is used or stored.
* **Non-Diagnostic Notice**: CareRelay organizes logistical records only and does not offer clinical diagnosis, prescribing advice, or therapeutic recommendations. All clinical decisions remain strictly between patients and qualified healthcare providers.

---

*Built with ❤️ for families caring across distances during the **Codebenders ACE Builders' Hackathon 2026**.*
