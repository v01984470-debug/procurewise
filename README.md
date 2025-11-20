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

## 📧 SendGrid Email Setup (PR Alerts)

To receive PR (Purchase Requisition) emails via SendGrid Inbound Parse:

### 1. Configure SendGrid Inbound Parse

1. **Login to SendGrid Dashboard** → Go to **Settings** → **Inbound Parse**
2. **Add a new hostname** (or use existing):

   - Hostname: `pr.yourdomain.com` (or your preferred subdomain)
   - **POST URL**: `https://your-domain.com/sendgrid-webhook`
     - For local testing: Use a service like [ngrok](https://ngrok.com/) to expose `http://localhost:8001/sendgrid-webhook`


3. **Update DNS Records**:
   - Add the MX record provided by SendGrid to your domain's DNS settings
   - This routes emails to SendGrid's servers

### 2. Environment Variables

Ensure your `.env` file includes:

```env
SENDGRID_API_KEY=your_sendgrid_api_key_here
```

### 3. Testing

- Send a test email to `pr@yourdomain.com` (or your configured email)
- The email will be automatically processed and saved to `code/updated_docs/pr_folders/pr_extractions/pr_ext.json`
- Query "Check email for PR Request" in the chat interface to view received emails

### 4. Webhook Endpoint

The webhook endpoint is available at:

- **POST** `/sendgrid-webhook`
- Accepts SendGrid Inbound Parse form data
- Automatically processes and saves PR emails

## 📋 Notes

- Keep API keys (OpenAI, SendGrid) in `.env` (not in version control)
- Update CSVs in `code/updated_docs/` to refresh analytics
- Windows users: Use `start.bat` or Developer PowerShell
- PR emails are stored in JSON format at `code/updated_docs/pr_folders/pr_extractions/pr_ext.json`
