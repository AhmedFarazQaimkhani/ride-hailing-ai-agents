# Deploy for free (no cost)

These platforms have **free tiers** you can use to host the Driver Co-Pilot web app. You only need to add your **OPENAI_API_KEY** in their dashboard if you want LLM-powered recommendations.

---

## 1. Render (recommended — easiest)

**Free tier:** 750 hours/month. App sleeps after ~15 min inactivity; first request after sleep can take ~30–60 sec.

1. Push your repo to **GitHub** (if not already).
2. Go to [render.com](https://render.com) → Sign up (free) → **New** → **Web Service**.
3. Connect your GitHub repo (e.g. `Ride Hailing Ai Agents` or the repo that contains it).
4. Set:
   - **Name:** `driver-copilot` (or any name)
   - **Root Directory:** leave blank, or the folder that contains `run_web.py`, `web/`, `core/`, etc. *(If the project is inside a subfolder, set Root Directory to that folder.)*
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python run_web.py`
5. Under **Environment** add:
   - **PORT** — Render sets this automatically; our app reads it.
   - **OPENAI_API_KEY** — your key (optional; if you want LLM recommendations).
6. Click **Create Web Service**. Wait for the first deploy. Your URL will be like `https://driver-copilot-xxxx.onrender.com`.

**Note:** If the project root is the repo root, leave Root Directory blank. If your repo has this project in a subfolder (e.g. `ride-hailing-agents/`), set Root Directory to `ride-hailing-agents`.

---

## 2. Railway

**Free tier:** Limited free usage per month (check [railway.app](https://railway.app) for current limits).

1. Go to [railway.app](https://railway.app) → Login with GitHub.
2. **New Project** → **Deploy from GitHub repo** → select your repo.
3. Set **Root Directory** if the app is in a subfolder.
4. Railway usually detects Python. Set:
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `python run_web.py`
5. In **Variables** add `OPENAI_API_KEY` (optional). Railway sets `PORT` automatically; our app uses it.
6. Deploy. Use the generated URL.

---

## 3. Fly.io

**Free tier:** Small VMs free (see [fly.io](https://fly.io) for limits).

1. Install [flyctl](https://fly.io/docs/hands-on/install-flyctl/) and run `fly auth login`.
2. In your project root (where `run_web.py` lives), run:
   ```bash
   fly launch
   ```
   Answer prompts (app name, region). Say no to Postgres/Redis if asked.
3. Create a `Dockerfile` in the project root:

   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   ENV PORT=8080
   EXPOSE 8080
   CMD ["sh", "-c", "python run_web.py"]
   ```

4. Set secrets (optional):
   ```bash
   fly secrets set OPENAI_API_KEY=sk-your-key
   ```
5. Deploy: `fly deploy`. Your app will be at `https://your-app-name.fly.dev`.

**Note:** Fly expects a Dockerfile or will generate one. The Dockerfile above assumes the app listens on `PORT` (we use 8080 as default in Docker; Fly sets `PORT`).

---

## 4. Vercel (serverless — API only or API + static)

**Free tier:** Generous for serverless and static.

- **Option A — API only:** Deploy the FastAPI app as a serverless function (e.g. with Mangum adapter). Frontend would need to call the deployed API URL.
- **Option B — Static on Vercel + API elsewhere:** Host the `web/static/` folder as a static site on Vercel and point it to your API (e.g. Render or Railway) for `/api/*` via proxy or env.

Simplest for “all in one” free: use **Render** or **Railway** so the same app serves both the UI and the API.

---

## Quick comparison

| Platform  | Free tier        | Sleep when idle? | Best for              |
|-----------|------------------|------------------|------------------------|
| **Render**| 750 hrs/month    | Yes (~15 min)    | Easiest, Git deploy   |
| **Railway** | Limited credits | Depends          | Simple, good DX       |
| **Fly.io**  | Small VMs       | No               | Always-on, need Docker |

---

## After deploy

- **OpenAI:** Add `OPENAI_API_KEY` in the platform’s Environment/Variables so the agents and Explainable Coach use the LLM.
- **URL:** Share the live URL (e.g. `https://your-app.onrender.com`) in your LinkedIn post or resume.
- **Cold start:** On Render, the first visit after sleep may be slow; the next loads are fast.
