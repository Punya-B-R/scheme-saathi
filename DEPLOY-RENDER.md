# Deploy Scheme Saathi on Render (step-by-step)

You will create **two** things on Render:
1. **Backend** (Web Service) – your Python API
2. **Frontend** (Static Site) – your React app

Then you’ll connect the frontend to the backend URL.

---

## Part 1: Push your code to GitHub

1. Create a new repo on GitHub (if you don’t have one): https://github.com/new  
2. Name it something like `scheme-saathi`.  
3. Don’t add a README if your project already has files.  
4. On your computer, in the project folder, run:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/scheme-saathi.git
   git push -u origin main
   ```
   Replace `YOUR_USERNAME` with your GitHub username.

---

## Part 2: Create the Backend on Render

1. Go to **https://render.com** and sign up or log in.  
2. Click **Dashboard** → **New** → **Web Service**.  
3. Connect your GitHub account if asked, then select the repo **scheme-saathi**.  
4. Configure the backend:
   - **Name:** `scheme-saathi-backend` (or any name you like)
   - **Region:** Pick the one closest to you (e.g. Oregon)
   - **Branch:** `main`
   - **Root Directory:** type `backend`  
     (So Render runs all commands from the backend folder.)
   - **Runtime:** **Python 3**
   - **Build Command:**  
     `pip install -r requirements.txt`  
     (Because Root Directory is `backend`, this uses `backend/requirements.txt`.)
   - **Start Command:**  
     `python run_server.py`

5. **Environment variables** (click **Advanced** → **Add Environment Variable** and add these one by one):

   | Key             | Value / what to put |
   |-----------------|---------------------|
   | `PYTHON_VERSION`| `3.11.9` (required for ChromaDB; do not use Python 3.14). doesn’t |
   | `GEMINI_API_KEY`| Your Gemini API key (from Google AI Studio). |
   | `DATABASE_URL`  | Your PostgreSQL connection string (e.g. from Render’s PostgreSQL or Supabase). |
   | `SUPABASE_URL`  | Your Supabase project URL (e.g. `https://xxxx.supabase.co`). |
   | `SUPABASE_JWT_SECRET` | Your Supabase JWT secret (Project Settings → API). |
   | `ALLOWED_ORIGINS` | Leave empty for now; we’ll set it after the frontend is deployed (see Part 4). |
   | `DEBUG`         | `0` (so the server doesn’t run in debug/reload mode). |

6. **Important:** Your schemes data must be in the repo so the backend can see it.
   - Make sure `backend/data_f/all_schemes.json` exists and is committed.
   - If the file is huge, you can use Git LFS or a smaller sample file for testing.

7. Click **Create Web Service**.  
8. Wait for the first deploy to finish.  
9. Copy the backend URL Render gives you, e.g. `https://scheme-saathi-backend.onrender.com` – you’ll need it for the frontend and CORS.

---

## Part 3: Create the Frontend on Render (Static Site)

1. In Render dashboard, click **New** → **Static Site**.  
2. Connect the **same** GitHub repo (**scheme-saathi**).  
3. Configure:
   - **Name:** `scheme-saathi-frontend`
   - **Branch:** `main`
   - **Root Directory:** leave **empty** (we build from repo root).
   - **Build Command:**  
     `cd frontend && npm install && npm run build`
   - **Publish Directory:**  
     `frontend/dist`  
     (This is where Vite puts the built files.)

4. **Environment variable** (so the frontend talks to your backend):
   - **Key:** `VITE_API_URL`  
   - **Value:** Your backend URL from Part 2, e.g. `https://scheme-saathi-backend.onrender.com`  
   - Do **not** add a trailing slash.

5. Click **Create Static Site**.  
6. Wait for the first deploy.  
7. Copy the frontend URL, e.g. `https://scheme-saathi-frontend.onrender.com`.

---

## Part 4: Allow frontend in backend CORS

1. Go back to your **backend** service on Render.  
2. Open **Environment** (or **Environment Variables**).  
3. Add or edit:
   - **Key:** `ALLOWED_ORIGINS`  
   - **Value:** Your frontend URL, e.g. `https://scheme-saathi-frontend.onrender.com`  
   - If you already had other origins (e.g. localhost), you can do:  
     `https://scheme-saathi-frontend.onrender.com,http://localhost:5173`

4. Save. Render will redeploy the backend. Wait for it to finish.

---

## Part 5: Check that it works

1. Open your **frontend** URL in the browser (e.g. `https://scheme-saathi-frontend.onrender.com`).  
2. Open the chat and send a message.  
3. If the AI replies and scheme cards load, you’re done.  
4. If something fails:
   - **Backend:** Open `https://YOUR-BACKEND-URL.onrender.com/health` – you should see JSON with `"status":"healthy"` (or similar) and `total_schemes` if data is loaded.  
   - **Frontend:** In the browser, open Developer Tools (F12) → **Network** tab, send a message, and see if the request to your backend URL returns 200 or an error.

---

## Quick checklist

- [ ] Code is on GitHub (with `backend/data_f/all_schemes.json` if you need schemes).  
- [ ] Backend Web Service: build = `pip install -r backend/requirements.txt`, start = `cd backend && python run_server.py`.  
- [ ] Backend env: `PYTHON_VERSION=3.11.9`, `GEMINI_API_KEY`, `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `ALLOWED_ORIGINS`, `DEBUG=0`. (Do not set `PORT` – Render sets it; the app uses it automatically.)  
- [ ] Frontend Static Site: build = `cd frontend && npm install && npm run build`, publish = `frontend/dist`.  
- [ ] Frontend env: `VITE_API_URL` = your backend URL (no trailing slash).  
- [ ] Backend `ALLOWED_ORIGINS` includes your frontend URL.

---

## If Render doesn’t have a “Python” Web Service

Some Render accounts use a **Dockerfile** instead. If you’re asked for a Dockerfile:

1. In your repo root, create a file named `Dockerfile` (no extension).  
2. Put in it (adjust if your structure is different):

   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   COPY backend/requirements.txt ./backend/
   RUN pip install --no-cache-dir -r backend/requirements.txt

   COPY backend/ ./backend/
   COPY backend/data_f/ ./backend/data_f/

   WORKDIR /app/backend
   ENV PORT=8000
   EXPOSE 8000
   CMD ["python", "run_server.py"]
   ```

3. In Render, choose **Docker** as the environment and leave build/start command empty so it uses the Dockerfile.

---

You’re done. Your app should be live at your frontend URL.
