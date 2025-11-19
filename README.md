<div align="center">

# ProcureWise ⚙️📦

**AI-assisted procurement co-pilot with FastAPI + Next.js**

</div>

## ✨ Overview

Unified workspace for supplier intelligence, PO tracking, inventory health, and shipment monitoring.

- **Backend:** FastAPI orchestrates LangChain + Autogen agents for procurement workflows
- **Frontend:** Next.js dashboard with chat interface and analytics
- **Data:** CSV datasets powering supplier analysis and cost modeling

## 🧰 Tech Stack

**Backend:** Python, FastAPI, Uvicorn, Pandas, LangChain, Autogen, SendGrid  
**Frontend:** Next.js 15, React 19, Tailwind, Radix UI, Recharts

## 🚀 Quick Start

### Setup

```bash
# Backend
cd code
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Frontend
cd ../Frontend
npm install
```

### Run

**Easiest:** Double-click `start.bat` in the repo root

- Backend starts on `http://localhost:8001`
- Frontend starts on `http://localhost:3000` (auto-opens browser)

**Manual:**

- Backend: `cd code && .venv\Scripts\python -m uvicorn app_entegris:app --reload --port 8001`
- Frontend: `cd Frontend && npm run dev`

## 🗂 Project Structure

| Path                          | Description                                        |
| ----------------------------- | -------------------------------------------------- |
| `code/app_entegris.py`        | Main FastAPI backend with agent workflows          |
| `code/app_entegris_backup.py` | Previous backend code (backup reference)           |
| `code/tools_manager.py`       | Data processing utilities & analytics              |
| `code/updated_docs/`          | CSV datasets (suppliers, PO, inventory, shipments) |
| `Frontend/app/`               | Next.js pages (dashboard, chat, alerts)            |
| `Frontend/components/`        | UI components (charts, tables, chat window)        |

## 📋 Notes

- Keep API keys (OpenAI, SendGrid) in `.env` (not in version control)
- Update CSVs in `code/updated_docs/` to refresh analytics
- Windows users: Use `start.bat` or Developer PowerShell
