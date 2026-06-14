import { useState } from "react";

const EXAMPLE_QUERIES = [
  "vintage graphic tee under $30",
  "90s track jacket in size M",
  "flowy midi skirt under $40",
  "black combat boots size 8",
  "designer ballgown size XXS under $5", // deliberate no-results test
];

const WARDROBE_CHOICES = ["Example wardrobe", "Empty wardrobe (new user)"];

const EMPTY_RESULT = { listing: "", outfit: "", fitCard: "" };

export default function App() {
  const [query, setQuery] = useState("");
  const [wardrobe, setWardrobe] = useState(WARDROBE_CHOICES[0]);
  const [result, setResult] = useState(EMPTY_RESULT);
  const [loading, setLoading] = useState(false);

  async function handleQuery() {
    if (!query.trim()) {
      setResult({ listing: "Please enter a query.", outfit: "", fitCard: "" });
      return;
    }
    setLoading(true);
    try {
      const resp = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, wardrobe }),
      });
      const data = await resp.json();
      setResult({
        listing: data.listing ?? "",
        outfit: data.outfit ?? "",
        fitCard: data.fitCard ?? "",
      });
    } catch (err) {
      setResult({ listing: `Request failed: ${err.message}`, outfit: "", fitCard: "" });
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e) {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleQuery();
  }

  return (
    <div className="app">
      <header>
        <h1>FitFindr 🛍️</h1>
        <p>
          Find secondhand pieces and get outfit ideas based on your wardrobe.
          Describe what you're looking for — include size and price if you want to filter.
        </p>
      </header>

      <div className="controls">
        <textarea
          className="query"
          placeholder="e.g. vintage graphic tee under $30, size M"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={onKeyDown}
          rows={2}
        />
        <div className="wardrobe">
          <span className="label">Wardrobe</span>
          {WARDROBE_CHOICES.map((choice) => (
            <label key={choice}>
              <input
                type="radio"
                name="wardrobe"
                value={choice}
                checked={wardrobe === choice}
                onChange={() => setWardrobe(choice)}
              />
              {choice}
            </label>
          ))}
        </div>
      </div>

      <button className="submit" onClick={handleQuery} disabled={loading}>
        {loading ? "Finding…" : "Find it"}
      </button>

      <div className="panels">
        <Panel title="🛍️ Top listing found" text={result.listing} />
        <Panel title="👗 Outfit idea" text={result.outfit} />
        <FitCardPanel text={result.fitCard} />
      </div>

      <div className="examples">
        <span className="label">Try these queries</span>
        <div className="example-chips">
          {EXAMPLE_QUERIES.map((q) => (
            <button
              key={q}
              className="chip"
              onClick={() => {
                setQuery(q);
                setWardrobe(WARDROBE_CHOICES[0]);
              }}
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function Panel({ title, text }) {
  return (
    <div className="panel">
      <span className="label">{title}</span>
      <textarea readOnly value={text} rows={8} />
    </div>
  );
}

function FitCardPanel({ text }) {
  const [image, setImage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const hasContent = text.trim().length > 0;
  const showImageBox = loading || image || error;

  async function generateImage() {
    setLoading(true);
    setError("");
    setImage("");
    try {
      const resp = await fetch(
        `/api/fit-image?description=${encodeURIComponent(text)}`
      );
      const data = await resp.json();
      if (!resp.ok || data.error) {
        setError(data.error || "Failed to generate image.");
      } else {
        setImage(data.image);
      }
    } catch (err) {
      setError(`Request failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="panel fit-card-panel">
      <div className="fit-card-header">
        <span className="label">✨ Your fit card</span>
        <button
          className="generate-image"
          onClick={generateImage}
          disabled={!hasContent || loading}
        >
          {loading ? "Generating…" : "Generate fit image"}
        </button>
      </div>
      <div className="fit-card-body">
        <textarea readOnly value={text} rows={8} />
        {showImageBox && (
          <div className={`image-box${loading ? " loading" : ""}`}>
            {loading ? (
              <div className="spinner" />
            ) : image ? (
              <img src={image} alt="Generated fit" />
            ) : (
              <span className="image-error">{error}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
