# FitFindr — React frontend

A React equivalent of the Gradio `app.py` UI. It renders the same query box,
wardrobe selector, three output panels, and example queries, and talks to the
Python agent through a small Flask bridge (`../server.py`).

## Run it

Two processes — backend then frontend.

### 1. Backend (Flask bridge)

From the project root:

```bash
pip install flask flask-cors      # in addition to requirements.txt
python server.py                  # serves the agent on http://localhost:5001
```

### 2. Frontend (Vite + React)

From this `web/` folder:

```bash
npm install
npm run dev                       # opens http://localhost:5173
```

The Vite dev server proxies `/api/*` to the Flask backend, so the React app
calls `run_agent()` exactly like the Gradio UI did via `handle_query()`.
