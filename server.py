"""
server.py

Thin Flask bridge that exposes the FitFindr agent to the React frontend.
This is the backend equivalent of what Gradio's handle_query() did in app.py:
it selects a wardrobe, calls run_agent(), and maps the session dict to the
three output panels.

Run with:
    python server.py

Then start the React app in web/ (see web/README.md). The Vite dev server
proxies /api requests here on port 5001.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS

from agent import run_agent
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

app = Flask(__name__)
CORS(app)


def _format_listing(item: dict) -> str:
    """Format a selected listing dict into readable text (mirrors app.py)."""
    if not item:
        return ""
    return "\n".join(
        [
            item.get("title", ""),
            "",
            item.get("description", ""),
            "",
            f"Size:      {item.get('size', '—')}",
            f"Price:     ${item.get('price', 0):.2f}",
            f"Condition: {item.get('condition', '—')}",
            f"Brand:     {item.get('brand') or '—'}",
            f"Platform:  {item.get('platform', '—')}",
        ]
    )


@app.post("/api/query")
def query():
    body = request.get_json(silent=True) or {}
    user_query = (body.get("query") or "").strip()
    wardrobe_choice = body.get("wardrobe", "Example wardrobe")

    # 1. Guard against an empty query.
    if not user_query:
        return jsonify(
            {
                "listing": "Please enter a query.",
                "outfit": "",
                "fitCard": "",
            }
        )

    # 2. Select the wardrobe.
    if wardrobe_choice == "Empty wardrobe (new user)":
        wardrobe = get_empty_wardrobe()
    else:
        wardrobe = get_example_wardrobe()

    # 3. Call the agent.
    session = run_agent(user_query, wardrobe)

    # 4. Map the session to the three panels.
    if session.get("error"):
        return jsonify({"listing": session["error"], "outfit": "", "fitCard": ""})

    return jsonify(
        {
            "listing": _format_listing(session.get("selected_item")),
            "outfit": session.get("outfit_suggestion") or "",
            "fitCard": session.get("fit_card") or "",
        }
    )


if __name__ == "__main__":
    app.run(port=5001, debug=True)
