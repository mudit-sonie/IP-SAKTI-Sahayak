import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

const exampleQuestions = [
  "Can I patent this formulation in India?",
  "Do I need ABS approval for this product?",
  "Can I register this product name as a trademark?",
];

function Ask() {
  const navigate = useNavigate();
  const location = useLocation();

  const jurisdiction = location.state?.jurisdiction || "india";
  const formulationCategory =
    location.state?.formulationCategory || "Not classified yet";

  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState(false);

function handleSubmit(event) {
  event.preventDefault();

  const cleanQuery = query.trim();

  if (!cleanQuery) {
    return;
  }

  navigate("/result", {
    state: {
      jurisdiction,
      formulationCategory,
      query: cleanQuery,
    },
  });
}

  return (
    <div className="classification-page">
      <div className="classification-container">
        <button
          className="text-back-button"
          onClick={() => navigate("/classify")}
        >
          ← Back to Classification
        </button>

        <div className="badge">ASK IP-SAKTI</div>

        <h1>
          Ask your <span>IP or regulatory question</span>
        </h1>

        <p className="classification-intro">
          IP-SAKTI will provide source-cited guidance based on your selected
          jurisdiction and formulation category.
        </p>

        <div className="context-card">
          <div>
            <span>Jurisdiction</span>
            <strong>
              {jurisdiction === "india" ? "🇮🇳 India" : "🌍 International"}
            </strong>
          </div>

          <div>
            <span>Formulation category</span>
            <strong>{formulationCategory}</strong>
          </div>
        </div>

        {!submitted ? (
          <form className="ask-card" onSubmit={handleSubmit}>
            <label htmlFor="query">Your question</label>

            <textarea
              id="query"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Example: Can I patent this formulation in India?"
              rows="6"
            />

            <p className="example-label">Try an example question</p>

            <div className="example-questions">
              {exampleQuestions.map((question) => (
                <button
                  type="button"
                  key={question}
                  className="example-question"
                  onClick={() => setQuery(question)}
                >
                  {question}
                </button>
              ))}
            </div>

            <button
              type="submit"
              className="next-button ask-submit-button"
              disabled={!query.trim()}
            >
              Get Source-Cited Guidance →
            </button>
          </form>
        ) : (
          <div className="result-card">
            <p className="result-label">Question ready</p>
            <h2>{query}</h2>

            <p className="classification-intro">
              Next, this question will be sent to the mock RAG result screen.
            </p>

            <button className="back-button" onClick={() => setSubmitted(false)}>
              Edit question
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default Ask;