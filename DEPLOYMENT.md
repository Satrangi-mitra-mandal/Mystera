# 🚀 DetectiveOS — Deployment Guide

This guide shows you exactly how to deploy:
- **Frontend** (HTML/CSS/JS) → **Vercel** (free)
- **Backend** (Python/FastAPI) → **Render** (free)
- **Database** (PostgreSQL) → **Render** (free, included with backend)

---

## The Big Picture

```
Your Users
    ↓  visits
Vercel  (frontend)
  https://detectiveos.vercel.app
    ↓  API calls (fetch requests)
Render  (backend API)
  https://detectiveos-api.onrender.com
    ↓  queries
Render PostgreSQL  (database)
  (managed automatically)
```

The frontend and backend are two separate deployments.
They talk to each other over HTTPS.
You connect them by putting the backend URL into the frontend's `api.js` file.

---

## Your Project Structure on GitHub

Your GitHub repo must look exactly like this:

```
detectiveos/                    ← repo root
│
├── vercel.json                 ← tells Vercel where the frontend is
├── render.yaml                 ← tells Render how to run the backend
├── .gitignore
├── README.md
│
├── frontend/                   ← Vercel deploys ONLY this folder
│   ├── index.html
│   ├── login.html
│   ├── cases.html
│   ├── case.html
│   ├── leaderboard.html
│   ├── profile.html
│   ├── css/
│   │   └── global.css
│   └── js/
│       ├── api.js              ← IMPORTANT: backend URL goes in here
│       └── board.js
│
├── backend/                    ← Render deploys ONLY this folder
│   ├── Procfile                ← tells Render the start command
│   ├── runtime.txt             ← Python 3.11
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── .env.example
│   ├── alembic/
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   └── tests/
│
└── case-templates/             ← JSON case files (used by seed.py)
    ├── midnight-manor.json
    ├── harbor-street-blackout.json
    ├── redwood-inheritance.json
    ├── double-exposure.json
    ├── zodiac-protocol.json
    └── glass-garden.json
```

---

## Step 1 — Push to GitHub

If you haven't already:

```bash
# In your detectiveos/ folder
git init
git add .
git commit -m "initial commit"

# Create a repo on github.com then:
git remote add origin https://github.com/YOUR-USERNAME/detectiveos.git
git push -u origin main
```

---

## Step 2 — Deploy Backend on Render

### 2a. Create a Render account
Go to https://render.com and sign up (free, no credit card needed).

### 2b. Create a PostgreSQL database
1. In Render dashboard → click **New +** → **PostgreSQL**
2. Name: `detectiveos-db`
3. Database: `detectiveos`
4. User: `detective`
5. Plan: **Free**
6. Click **Create Database**
7. Wait ~1 minute. Then copy the **Internal Database URL** — you'll need it next.

### 2c. Create a Web Service for the backend
1. In Render dashboard → click **New +** → **Web Service**
2. Connect your GitHub repo
3. Fill in the settings:

| Setting | Value |
|---------|-------|
| Name | `detectiveos-api` |
| Root Directory | `backend` |
| Environment | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Plan | **Free** |

4. Click **Advanced** → **Add Environment Variable** and add these one by one:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Paste the Internal Database URL from Step 2b |
| `ANTHROPIC_API_KEY` | Your Claude API key from console.anthropic.com |
| `JWT_SECRET` | Any long random string (e.g. `detective-xyz-secret-2026-abc`) |
| `JWT_ALGORITHM` | `HS256` |
| `JWT_EXPIRE_MINUTES` | `10080` |
| `ENVIRONMENT` | `production` |
| `CORS_ORIGINS` | Leave blank for now — you'll fill this in Step 4 |

5. Click **Create Web Service**
6. Render will build and deploy. This takes 2–4 minutes.
7. When done, you'll see a green **Live** status and a URL like:
   ```
   https://detectiveos-api.onrender.com
   ```
   **Copy this URL — you need it in Step 3.**

### 2d. Seed the database
After the first successful deploy, you need to load the 6 cases into the database.

1. In the Render dashboard, open your `detectiveos-api` service
2. Go to the **Shell** tab
3. Run these commands:

```bash
cd /app
alembic upgrade head
python -m app.db.seed
```

You should see:
```
✓ Created demo user: detective@demo.com / password123
✓ Seeded case: The Midnight Manor Incident
... (all 6 cases)
✅ Database seeded successfully.
```

> **Only run seed once.** Running it again will skip already-existing cases.

### 2e. Test your backend
Open your browser and visit:
```
https://detectiveos-api.onrender.com/api/health
```

You should see:
```json
{"status": "ok", "service": "DetectiveOS API", "version": "1.0.0"}
```

If you see that — your backend is live. ✅

---

## Step 3 — Connect Frontend to Backend

**This is the most important step.**

Open `frontend/js/api.js` in your code editor and find this line near the top:

```javascript
const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? 'http://localhost:8000'
  : 'https://YOUR-BACKEND-URL.onrender.com'; // ← REPLACE THIS
```

Replace `YOUR-BACKEND-URL.onrender.com` with your actual Render URL from Step 2c.

For example, if your Render URL is `https://detectiveos-api.onrender.com`, it becomes:

```javascript
const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? 'http://localhost:8000'
  : 'https://detectiveos-api.onrender.com'; // ✅ real URL
```

Save the file, then commit and push:

```bash
git add frontend/js/api.js
git commit -m "connect frontend to backend"
git push
```

---

## Step 4 — Deploy Frontend on Vercel

### 4a. Create a Vercel account
Go to https://vercel.com and sign up with your GitHub account (free).

### 4b. Import your project
1. In Vercel dashboard → click **Add New** → **Project**
2. Find your `detectiveos` repo and click **Import**
3. Vercel will detect the `vercel.json` file automatically

### 4c. Configure the deployment

| Setting | Value |
|---------|-------|
| Framework Preset | **Other** |
| Root Directory | Leave blank (Vercel uses `vercel.json`) |
| Build Command | Leave blank |
| Output Directory | Leave blank |
| Install Command | Leave blank |

4. Click **Deploy**
5. After 30–60 seconds, you'll get a URL like:
   ```
   https://detectiveos.vercel.app
   ```
   **Copy this URL — you need it in Step 5.**

---

## Step 5 — Set CORS on the Backend

The backend needs to know your Vercel URL so it allows requests from it.

1. Go back to **Render dashboard** → your `detectiveos-api` service
2. Go to **Environment** tab
3. Find the `CORS_ORIGINS` variable and set it to your Vercel URL:

```
https://detectiveos.vercel.app
```

4. Click **Save Changes** — Render will automatically redeploy.

---

## Step 6 — Test the Full Connection

1. Open your Vercel URL: `https://detectiveos.vercel.app`
2. Click **Sign In**
3. Log in with the demo account:
   - Email: `detective@demo.com`
   - Password: `password123`
4. Click **Open Cases** — you should see all 6 mystery cases
5. Open a case and try interrogating a suspect

If it works — you're fully deployed! 🎉

---

## Troubleshooting

### "Failed to fetch" or network error on the frontend
**Cause:** The backend URL in `api.js` is wrong, or the backend isn't running.
**Fix:**
- Open your browser DevTools (F12) → Network tab
- Click a button that makes an API call
- Look at the request — what URL is it calling?
- Make sure it matches your Render URL exactly
- Check that your Render service shows **Live** (green)

### "CORS error" in the browser console
**Cause:** The backend is rejecting requests because your Vercel URL isn't in `CORS_ORIGINS`.
**Fix:**
- Go to Render → your service → Environment
- Set `CORS_ORIGINS` to your exact Vercel URL (no trailing slash)
- Example: `https://detectiveos.vercel.app`
- Redeploy

### Backend returns 500 error
**Cause:** Usually a missing environment variable (especially `DATABASE_URL` or `ANTHROPIC_API_KEY`).
**Fix:**
- Go to Render → your service → Logs
- Read the error message
- Check all environment variables are set correctly

### Render backend is slow to respond the first time
**Cause:** Render free tier spins down your service after 15 minutes of inactivity.
**Fix:** This is normal on the free tier. The first request after inactivity takes ~30 seconds to wake up. Subsequent requests are fast. If you want it always-on, upgrade to a paid plan.

### Vercel deployment failed
**Cause:** Usually `vercel.json` is misconfigured or in the wrong place.
**Fix:**
- Make sure `vercel.json` is in the **root** of your repo (not inside `frontend/`)
- The file should exist at: `detectiveos/vercel.json`

### "relation does not exist" database error
**Cause:** Migrations haven't run yet.
**Fix:** Go to Render Shell and run:
```bash
alembic upgrade head
```

### Cases not appearing
**Cause:** Seed script hasn't run yet.
**Fix:** Go to Render Shell and run:
```bash
python -m app.db.seed
```

---

## Updating Your App

Whenever you make changes to the code:

**For frontend changes:**
```bash
git add .
git commit -m "your change description"
git push
```
Vercel automatically redeploys. Takes ~30 seconds.

**For backend changes:**
```bash
git add .
git commit -m "your change description"
git push
```
Render automatically redeploys. Takes ~2 minutes.

---

## Environment Variables Summary

### Backend (set in Render dashboard)

| Variable | What it is | Where to get it |
|----------|-----------|----------------|
| `DATABASE_URL` | PostgreSQL connection string | Render provides it (Internal Database URL) |
| `ANTHROPIC_API_KEY` | Claude AI key | https://console.anthropic.com |
| `JWT_SECRET` | Token signing key | Any long random string |
| `JWT_ALGORITHM` | Always `HS256` | Just type `HS256` |
| `JWT_EXPIRE_MINUTES` | Login session length | Use `10080` (7 days) |
| `ENVIRONMENT` | `production` | Just type `production` |
| `CORS_ORIGINS` | Your Vercel URL | From Step 4 |

### Frontend (no environment variables)
The frontend is plain HTML/JS with no build step, so there are no environment variables.
The only "config" is the `API_BASE` URL in `frontend/js/api.js`.

---

## Final Checklist

- [ ] Code pushed to GitHub
- [ ] Render PostgreSQL database created
- [ ] Render web service created with all environment variables set
- [ ] `alembic upgrade head` run in Render shell
- [ ] `python -m app.db.seed` run in Render shell
- [ ] Backend health check passes: `https://your-api.onrender.com/api/health`
- [ ] `frontend/js/api.js` updated with real Render URL
- [ ] Change committed and pushed
- [ ] Vercel project imported and deployed
- [ ] `CORS_ORIGINS` set in Render to Vercel URL
- [ ] Login with `detective@demo.com / password123` works
- [ ] All 6 cases visible on the cases page

---

## Your Live URLs

Once deployed, fill these in:

| | URL |
|---|---|
| Frontend | `https://_________________.vercel.app` |
| Backend API | `https://_________________.onrender.com` |
| API Docs | `https://_________________.onrender.com/api/docs` |
| Health Check | `https://_________________.onrender.com/api/health` |
