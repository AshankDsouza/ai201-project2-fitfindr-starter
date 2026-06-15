"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

from __future__ import annotations

import json
import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()
GROQ_MODEL = "llama-3.3-70b-versatile"



# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)

# ── Tool 0: get filter criteria values ─────────────────────────────────────────────────
def get_filter_criteria_values(natural_language_query: str) -> dict:
    prompt = f"""Extract the description, size, and max_price from the following user query. If any of these parameters are not specified in the query, set them to null.
    Please return the result as a JSON object with the following format:

    Output schema:
    {{
        "description": str,   # e.g. "vintage graphic tee",
        "size": str | None,  # e.g. "M" or None if not specified
        "max_price": float | None,  # e.g. 30.0 or None if not specified
    }}

    User query: {natural_language_query}
    """

    client = _get_groq_client()
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    content = resp.choices[0].message.content

    try:
        query_dict = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        # Fallback: pull the first {...} block out of the text and parse it.
        match = re.search(r"\{.*\}", content or "", re.DOTALL)
        query_dict = json.loads(match.group(0)) if match else {}
    
    return query_dict

# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    # Replace this with your implementation

    listings = load_listings()
    if size is not None:
        listings = [listing for listing in listings if listing['size'] == size]
    if max_price is not None:
        listings = [listing for listing in listings if listing['price'] <= max_price]

    scored_listings = []
    for listing in listings:
        score = sum(1 for keyword in description.split() if keyword.lower() in listing['description'].lower())
        if score > 0:
            scored_listings.append((score, listing))

    scored_listings.sort(key=lambda x: x[0], reverse=True)
    return [listing for _, listing in scored_listings]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict | None, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """



    # Replace this with your implementation
    if not wardrobe['items'] or not new_item:
        # Call LLM with general styling advice prompt
        return "Black and white is a safe choice. Other color pairings should be based on common color theory rules."


    SYSTEM_PROMPT =  "Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits."
    
    context_blocks = ["The new item the user is considering buying is:"]
    context_blocks.append(
        f"- Title: {new_item['title']}\n"
        f"- Description: {new_item['description']}\n"
        f"- Category: {new_item['category']}\n"
        f"- Style Tags: {', '.join(new_item['style_tags'])}\n"
        f"- Size: {new_item['size']}\n"
        f"- Condition: {new_item['condition']}\n"
        f"- Price: ${new_item['price']:.2f}\n"
        f"- Colors: {', '.join(new_item['colors'])}\n"
        f"- Brand: {new_item['brand']}\n"
        f"- Platform: {new_item['platform']}"
    )


    context_blocks.append("The clothing items in the user's wardrobe are:")

    print("wardrobe items:", wardrobe['items'])  # Debug print to check wardrobe contents

    for idx, item in enumerate(wardrobe['items']):
        block = (
            f"Item {idx + 1}:\n"
            f"- Name: {item['name']}\n"
            f"- Category: {item['category']}\n"
            f"- Colors: {', '.join(item['colors'])}\n"
            f"- Style Tags: {', '.join(item['style_tags'])}\n"
            f"- Notes: {item.get('notes') or 'N/A'}"
        )
        context_blocks.append(block)

    context = "\n\n".join(context_blocks)

    question = "Based on the users existing clothing items and the new item, suggest 1-2 complete outfits. Be specific about which items to pair together and why, and mention the vibe or occasion each outfit suits."

    user_prompt = (
        f"Context passages:\n\n{context}\n\n"
        f"Question: {question}\n\n"
    )

    client = _get_groq_client()
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
    )
    

    return resp.choices[0].message.content


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    if not outfit or not outfit.strip():
        return "Could not create a fit due to insufficient information."

    prompt = (
        f"Write a 2-4 sentence, short, shareable description of a complete outfit — the kind of thing someone would caption an Instagram post with.\n\n"
        f"Item: {new_item['title']} — ${new_item['price']:.2f} on {new_item['platform']}\n"
        f"Outfit: {outfit}\n\n"
        "Make it casual and authentic like a real OOTD post. Mention the item name, price, and platform naturally once each. Capture the outfit vibe in specific terms."
    )

    client = _get_groq_client()
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
    )
    return resp.choices[0].message.content
