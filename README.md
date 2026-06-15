# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here

Have docker installed on your system and run:

```bash
bash run_app.sh
```


## Tools

### Required

#### 1. `search_listings(description, size, max_price)`

Searches the mock listings dataset for items matching a description, an optional size, and an optional price ceiling.

**Inputs:**
- `description` (`str`): keywords describing what the user is looking for (e.g., `"vintage graphic tee"`).
- `size` (`str | None`): size string to filter by, or `None` to skip size filtering. Matching is case-insensitive.
- `max_price` (`float | None`): maximum price (inclusive), or `None` to skip price filtering.

**Returns:** `list[dict]` — a list of matching listing dicts, sorted by relevance (best keyword match first). Returns an empty list if nothing matches (never raises). Each listing dict contains: `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand`, and `platform`.

#### 2. `suggest_outfit(new_item, wardrobe)`

Given a thrifted item and the user's wardrobe, suggests 1–2 complete outfits using an LLM.

**Inputs:**
- `new_item` (`dict`): a listing dict — the item the user is considering buying.
- `wardrobe` (`dict`): a wardrobe dict with an `items` key containing a list of wardrobe item dicts. May be empty.

**Returns:** `str` — a non-empty string with outfit suggestions describing which pieces to pair together, why, and the vibe/occasion each outfit suits. If the wardrobe is empty, returns general styling advice instead.

#### 3. `create_fit_card(outfit, new_item)`

Generates a short, shareable OOTD-style caption for the thrifted find.

**Inputs:**
- `outfit` (`str`): the outfit suggestion string from `suggest_outfit()`.
- `new_item` (`dict`): the listing dict for the thrifted item.

**Returns:** `str` — a casual, 2–4 sentence Instagram/TikTok caption that mentions the item name, price, and platform once each and captures the outfit's vibe. If `outfit` is empty or whitespace-only, returns a descriptive error message string (never raises).

### Extra

#### `get_filter_criteria_values(natural_language_query)`

Uses an LLM to extract structured search filters from a free-form user query.

**Inputs:**
- `natural_language_query` (`str`): the raw user query (e.g., `"a vintage tee in size M under $30"`).

**Returns:** `dict` — a JSON object with the keys `description` (`str`), `size` (`str | None`), and `max_price` (`float | None`). Fields not specified in the query are set to `None`. These values are intended to be passed directly into `search_listings`.

## Multi-Step Workflow End to End

1. Query with everything correct
example: "vintage graphic tee under $30"

Steps agent takes:
i. parses the query for search filter parameters
ii. calls search_listings() with filter parameters
iii. generates outfit suggestion with the top result generated above along with the user wardrobe with suggest_outfit()
iv. generates fit card with create_fit_card() passing the outfit and selected item

2. Query with nothing found by the search_listings call
example: "designer ballgown size XXS under $5"

i. parses the query for search filter parameters
ii. calls search_listings() with filter parameters and it returns empty
iii. generates outfit_suggestion with a generic fallback suggestion
iv. no call to fit card tool 

## State Management Across Tool Calls

FitFindr never asks the user to re-enter information between tool calls. All state for a single interaction lives in one **session dict**, created once per run by `_new_session()` in [agent.py](agent.py#L31) and threaded through the three tools by `run_agent()`.

### What is stored, and when

The session dict (see [agent.py:41-50](agent.py#L41-L50)) is the single source of truth for a run. Fields are populated as the workflow progresses:

| Field | Set when | Source |
|-------|----------|--------|
| `query` | session init | original user query |
| `parsed` / extracted filters | after parsing | `get_filter_criteria_values()` |
| `search_results` | after search | `search_listings()` |
| `selected_item` | after search | top result of `search_listings()` |
| `wardrobe` | session init | passed into `run_agent()` |
| `outfit_suggestion` | after styling | `suggest_outfit()` |
| `fit_card` | after captioning | `create_fit_card()` |
| `error` | on early exit | set if a step fails (e.g., no listings) |

### How state passes between tools

The output of each tool becomes the input to the next — no re-entry by the user:

1. **`search_listings` → `suggest_outfit`.** The top listing returned by `search_listings()` is stored in `session["selected_item"]`, then passed directly into `suggest_outfit()`:
   ```python
   listings = search_listings(description, size=None, max_price=None)
   new_session["selected_item"] = listings[0]
   ...
   suggestion = suggest_outfit(new_session["selected_item"], wardrobe)
   ```
   The *same* item dict found by the search is the one styled — see [agent.py:109-132](agent.py#L109-L132).

2. **`suggest_outfit` → `create_fit_card`.** The outfit string stored in `session["outfit_suggestion"]` is passed straight into `create_fit_card()`, along with the same selected item:
   ```python
   new_session["outfit_suggestion"] = suggestion
   fit_card = create_fit_card(new_session["outfit_suggestion"], new_session["selected_item"])
   new_session["fit_card"] = fit_card
   ```
   See [agent.py:132-137](agent.py#L132-L137).

Because every intermediate result is written back into the session dict and read from it by the next step, the user enters their query exactly once. `run_agent()` returns the fully populated session dict so callers can read any field (`selected_item`, `outfit_suggestion`, `fit_card`, or `error`).

## Planning Loop Adaptiveness

The agent does **not** call all three tools unconditionally. `run_agent()` in [agent.py:55](agent.py#L55) inspects the session state after each step and branches based on what it finds. There are three decision points:

### Decision 1 — Was a description extracted?

After `get_filter_criteria_values()` parses the query, the loop checks whether a `description` was found:

```python
if not description:
    new_session["error"] = "Could not extract a description from the query."
    return new_session
```

If the LLM could not extract a searchable description, the loop sets `error` and **returns immediately** — `search_listings`, `suggest_outfit`, and `create_fit_card` are all skipped ([agent.py:103-105](agent.py#L103-L105)).

### Decision 2 — Did `search_listings` return any results?

This is the key adaptive branch. The loop checks whether the search produced a top result:

```python
listings = search_listings(description, size=None, max_price=None)
top_result = listings[0] if listings else None
if not top_result:
    new_session["error"] = "No listings found matching the query criteria."
    suggestion = suggest_outfit(None, wardrobe)
    new_session["outfit_suggestion"] = suggestion
    return new_session
new_session["selected_item"] = top_result
```

**When `search_listings` returns no results**, the agent does *not* proceed down the happy path. Instead it:
1. Sets `session["error"]` to `"No listings found matching the query criteria."`
2. Calls `suggest_outfit(None, wardrobe)` to produce **general fallback styling advice** (with no specific item),
3. **Skips `create_fit_card` entirely** — there is no item to caption — and returns early.

See [agent.py:109-115](agent.py#L109-L115).

### Decision 3 — Happy path

Only when a `selected_item` exists does the loop continue to call `suggest_outfit()` with the real item and then `create_fit_card()` ([agent.py:131-137](agent.py#L131-L137)).

### Happy path vs. non-standard input

The two paths call a different set of tools in a different sequence:

| Step | Happy path (`"vintage graphic tee under $30"`) | No-results (`"designer ballgown size XXS under $5"`) |
|------|------------------------------------------------|------------------------------------------------------|
| Parse query | ✅ `get_filter_criteria_values()` | ✅ `get_filter_criteria_values()` |
| Search | ✅ `search_listings()` → ≥1 result | ✅ `search_listings()` → **empty** |
| Select item | ✅ top result → `selected_item` | ❌ no item; `error` set |
| Suggest outfit | ✅ `suggest_outfit(item, wardrobe)` | ⚠️ `suggest_outfit(None, wardrobe)` — generic advice |
| Create fit card | ✅ `create_fit_card(...)` | ❌ **skipped** |
| Return | full session with `fit_card` | early return, `fit_card` is `None` |

The CLI test in [agent.py:145-165](agent.py#L145-L165) demonstrates both paths back to back, confirming the agent behaves differently for the no-results input than for the happy path.

## Error Handling

Each of the three required tools has a specific failure mode it guards against, and the agent responds to each without crashing.

### 1. `search_listings` — no matching items

**Failure mode:** the query is valid but nothing in the dataset matches the description, size, or price ceiling. The tool returns an **empty list** rather than raising ([tools.py:113-128](tools.py#L113-L128)).

**What the agent does:** `run_agent()` detects the empty result (`top_result = listings[0] if listings else None`), sets `session["error"]` to `"No listings found matching the query criteria."`, falls back to general styling advice via `suggest_outfit(None, wardrobe)`, and skips `create_fit_card` — returning early instead of styling a nonexistent item ([agent.py:109-115](agent.py#L109-L115)).

### 2. `suggest_outfit` — empty wardrobe

**Failure mode:** the user has no wardrobe items (`wardrobe["items"]` is empty), so there are no pieces to pair the new item with. Building an outfit from named wardrobe pieces is impossible.

**What the agent does:** the tool guards against this up front and returns **general styling advice** instead of raising or returning an empty string ([tools.py:162-164](tools.py#L162-L164)). The agent stores this string in `session["outfit_suggestion"]` and proceeds normally, so the user always gets usable guidance.

### 3. `create_fit_card` — empty/missing outfit

**Failure mode:** the outfit string passed in is empty or whitespace-only (e.g., an upstream styling step produced nothing), so there is no outfit to caption.

**What the agent does:** the tool checks `if not outfit or not outfit.strip()` and returns the descriptive message `"Could not create a fit due to insufficient information."` rather than raising ([tools.py:251-252](tools.py#L251-L252)). This string is stored in `session["fit_card"]`, so the run completes cleanly with an informative result.

### Run-level guard

Beyond the per-tool failures, `run_agent()` also handles an unparseable query: if `get_filter_criteria_values()` returns no `description`, it sets `session["error"]` and returns before any tool is called ([agent.py:103-105](agent.py#L103-L105)). In every case the failure is recorded in the session dict (`error` and/or a fallback string) rather than surfacing as an exception.


## AI usage 

### Instance 1

#### Directed: 
Add an image generation tool based on the content in outfit tool
#### Reviewed, revised, or overrode: 
Image generation AI models are not free and instead scrapped the feature and instead opted for a bing based web scrapper that does an image search


### Instance 2

#### Directed: 
Do parsing of the query.
#### Reviewed, revised, or overrode: 
replaced the regex based parsing with an LLM based parsing. 


## Spec reflection

**One way the spec helped.** The starter spec prescribed a single **session dict** as the source of truth, with each tool's output feeding the next tool's input (`search_listings` → `suggest_outfit` → `create_fit_card`). This made state management almost trivial to reason about: there was never any question of where a value lived or how it reached the next step, since everything is written back into one dict and `run_agent()` simply reads from it. It also made the planning loop's early-exit branches clean — setting `session["error"]` and returning is enough to communicate failure to the caller.

**One divergence and why.** The spec suggested parsing the query with regex or string splitting (see Step 2 of `run_agent()` in [agent.py:75-77](agent.py#L75-L77)). We diverged by adding an LLM-based parser, `get_filter_criteria_values()` ([tools.py:43-76](tools.py#L43-L76)), which extracts `description`, `size`, and `max_price` into structured JSON. Regex was too brittle for free-form phrasing ("a vintage tee in size M for under thirty bucks"), whereas the LLM reliably normalizes varied phrasing and returns `None` for unspecified fields. This is also why the README documents `get_filter_criteria_values` as an extra tool beyond the three required ones.

