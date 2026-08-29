import { useLocation, useNavigate } from "react-router-dom";

function Result() {
  const navigate = useNavigate();
  const location = useLocation();

  const jurisdiction = location.state?.jurisdiction || "india";
  const formulationCategory =
    location.state?.formulationCategory || "Not classified";
  const query = location.state?.query || "No question was submitted.";

  const asksAboutIndia = /\bindia\b/i.test(query);
  const jurisdictionMismatch =
    jurisdiction === "international" && asksAboutIndia;

  const absTriggered = /biological|plant|herb|genetic|resource/i.test(query);

  const sources =
    jurisdiction === "india"
      ? [
          {
            source: "Patents Act, 1970",
            section: "Section 3(p)",
            detail: "Traditional-knowledge patentability consideration",
          },
          {
            source: "Biological Diversity Act, 2002",
            section: "Section 3",
            detail: "Access and benefit-sharing consideration",
          },
        ]
      : [
          {
            source: "TRIPS Agreement",
            section: "Article 27",
            detail: "International patentability framework",
          },
          {
            source: "Convention on Biological Diversity",
            section: "Article 15",
            detail: "Access to genetic resources framework",
          },
        ];

  const answer =
    jurisdiction === "india"
      ? "This is a mock India-focused response. The production system will retrieve relevant statutory sections from the India corpus, then generate a source-cited explanation based only on those retrieved materials."
      : "This is a mock international response. The production system will retrieve relevant treaty provisions from the international corpus, then generate a source-cited explanation based only on those retrieved materials.";

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

        <p className="result-question">“{query}”</p>

        <div className="result-context">
          <span>
            {jurisdiction === "india" ? "🇮🇳 India" : "🌍 International"}
          </span>
          <span>{formulationCategory}</span>
        </div>

        {jurisdictionMismatch && (
          <div className="mismatch-card">
            <strong>Jurisdiction check:</strong> You selected International,
            but your question mentions India. In the production system, the
            assistant would ask you to confirm the jurisdiction before giving
            jurisdiction-specific guidance.
          </div>
        )}

        <section className="answer-card">
          <div className="answer-heading">
            <div>
              <p className="result-label">Mock response</p>
              <h2>Guidance</h2>
            </div>

            <span className="confidence-badge">High confidence (demo)</span>
          </div>

          <p className="answer-text">{answer}</p>

          <p className="mock-notice">
            This screen is using mock data. The backend will later return the
            real answer, citations, retrieval score, and confidence status.
          </p>
        </section>

        <section className="sources-section">
          <h2>Sources used</h2>

          <div className="citation-list">
            {sources.map((citation) => (
              <article className="citation-card" key={citation.source}>
                <p>{citation.source}</p>
                <strong>{citation.section}</strong>
                <span>{citation.detail}</span>
              </article>
            ))}
          </div>
        </section>

        <section
          className={absTriggered ? "abs-card triggered" : "abs-card"}
        >
          <h2>ABS consideration</h2>

          {absTriggered ? (
            <p>
              This mock query may involve biological resources. The production
              system will run an additional ABS-specific retrieval pass.
            </p>
          ) : (
            <p>
              No ABS-specific trigger was found in this mock question.
            </p>
          )}
        </section>

        <section className="escalation-card">
          <h2>Need specialist support?</h2>
          <p>
            If source support is weak or confidence is low, IP-SAKTI will
            recommend escalation to a human IP facilitator instead of guessing.
          </p>
        </section>

        <button className="next-button result-button" onClick={() => navigate("/")}>
          Start a New Query →
        </button>
      </div>
    </div>
  );
}

export default Result;