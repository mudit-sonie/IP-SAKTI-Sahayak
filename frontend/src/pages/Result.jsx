import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { query as runQuery } from "../api/client";

function ConfidenceBadge({ confidence }) {
  if (!confidence) return null;
  const { status, retrieval_score, self_confidence } = confidence;
  const answered = status === "answered";
  return (
    <span className={answered ? "confidence-badge" : "confidence-badge low"}>
      {answered ? "Answered" : "Escalated"} · retrieval{" "}
      {Math.round((retrieval_score ?? 0) * 100)}% · model {self_confidence}
    </span>
  );
}

function Result() {
  const navigate = useNavigate();
  const location = useLocation();

  const jurisdiction = location.state?.jurisdiction || "india";
  const formulationCategory = location.state?.formulationCategory || null;
  const formulationLabel =
    location.state?.formulationLabel || formulationCategory || "Not classified";
  const question = location.state?.query || "";

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!question) {
      setError("No question was submitted.");
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    runQuery(
      { query: question, jurisdiction, formulationCategory },
      { signal: controller.signal },
    )
      .then((res) => setData(res))
      .catch((err) => {
        if (err.name === "AbortError") return;
        setError(err.message || "The query failed.");
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [question, jurisdiction, formulationCategory]);

  const escalated = data?.confidence?.status === "escalate";

  return (
    <div className="classification-page">
      <div className="classification-container">
        <button className="text-back-button" onClick={() => navigate("/ask")}>
          ← Edit question
        </button>

        <div className="badge">SOURCE-CITED GUIDANCE</div>

        <h1>
          Your <span>IP-SAKTI response</span>
        </h1>

        <p className="result-question">“{question}”</p>

        <div className="result-context">
          <span>{jurisdiction === "india" ? "🇮🇳 India" : "🌍 International"}</span>
          <span>{formulationLabel}</span>
        </div>

        {loading && (
          <section className="answer-card">
            <p className="answer-text">
              Retrieving statutory provisions and generating a source-cited
              answer… this usually takes a few seconds.
            </p>
          </section>
        )}

        {error && !loading && (
          <div className="mismatch-card">
            <strong>Something went wrong:</strong> {error}
            <div style={{ marginTop: "0.75rem" }}>
              <button
                className="back-button"
                onClick={() => navigate("/ask", { state: location.state })}
              >
                Try again
              </button>
            </div>
          </div>
        )}

        {data && !loading && !error && (
          <>
            <section className="answer-card">
              <div className="answer-heading">
                <div>
                  <p className="result-label">
                    {escalated ? "Escalation" : "Guidance"}
                  </p>
                  <h2>{escalated ? "Routed to a human facilitator" : "Answer"}</h2>
                </div>
                <ConfidenceBadge confidence={data.confidence} />
              </div>

              <p className="answer-text">{data.answer}</p>
            </section>

            <section className="sources-section">
              <h2>Sources used</h2>
              {data.citations?.length ? (
                <div className="citation-list">
                  {data.citations.map((c, i) => (
                    <article
                      className="citation-card"
                      key={c.excerpt_ref || `${c.source}-${c.section}-${i}`}
                    >
                      <p>{c.source}</p>
                      <strong>
                        {/^\s*(section|article)/i.test(c.section)
                          ? c.section
                          : `Section ${c.section}`}
                      </strong>
                      {c.excerpt_ref && <span>ref: {c.excerpt_ref}</span>}
                    </article>
                  ))}
                </div>
              ) : (
                <p className="mock-notice">
                  No passage met the citation bar for this question — the
                  assistant did not invent one.
                </p>
              )}
            </section>

            <section className={data.abs_flag ? "abs-card triggered" : "abs-card"}>
              <h2>ABS consideration</h2>
              {data.abs_flag ? (
                <p>
                  {data.abs_note ||
                    "This query touches biological resources — an ABS-specific retrieval pass over the Biological Diversity Act was run."}
                </p>
              ) : (
                <p>No access-and-benefit-sharing trigger was found in this question.</p>
              )}
            </section>

            {escalated && (
              <section className="escalation-card">
                <h2>Need specialist support?</h2>
                <p>
                  Retrieval support or model confidence was below threshold, so
                  IP-SAKTI is recommending escalation to a human IP facilitator
                  rather than guessing.
                </p>
              </section>
            )}
          </>
        )}

        <button
          className="next-button result-button"
          onClick={() => navigate("/")}
        >
          Start a New Query →
        </button>
      </div>
    </div>
  );
}

export default Result;
