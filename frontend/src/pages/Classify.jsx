import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { classify } from "../api/client";

// Human-readable labels for the backend FormulationCategory enum.
const CATEGORY_LABELS = {
  classical: "Classical Ayurvedic Medicine",
  proprietary: "Patent / Proprietary Ayurvedic Medicine",
  new_drug: "New Drug",
  phytopharmaceutical: "Phytopharmaceutical Drug",
  ayurveda_aahar: "Ayurveda Aahara / Nutraceutical",
  cosmetic: "Cosmetic",
};

const CATEGORY_BLURB = {
  classical:
    "Your product tracks an authoritative textual formulation. Traditional-knowledge and non-patentability considerations will matter most.",
  proprietary:
    "All ingredients are textual but the combination or indication is new — a patent/proprietary Ayurvedic medicine pathway.",
  new_drug:
    "Your product includes a new chemical entity. Safety, efficacy and new-drug approval requirements are likely relevant.",
  phytopharmaceutical:
    "Your active is a standardised botanical extract/fraction — the phytopharmaceutical drug pathway.",
  ayurveda_aahar:
    "Your product aligns with the Ayurveda Aahara / nutraceutical regulatory pathway.",
  cosmetic: "Your product aligns with the cosmetic regulatory category.",
};

function Classify() {
  const navigate = useNavigate();
  const location = useLocation();
  const jurisdiction = location.state?.jurisdiction || "india";

  const [answers, setAnswers] = useState({});
  const [step, setStep] = useState(0); // number of questions answered so far
  const [question, setQuestion] = useState(null);
  const [category, setCategory] = useState(null);
  const [selected, setSelected] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const history = useRef([]); // answers snapshots, for the Back button

  const advance = useCallback(async (nextAnswers) => {
    setLoading(true);
    setError(null);
    try {
      const res = await classify(nextAnswers);
      if (res.complete) {
        setCategory(res.formulation_category);
        setQuestion(null);
      } else {
        setQuestion(res.next_question);
        setCategory(null);
      }
      setSelected("");
    } catch (err) {
      setError(err.message || "Classification failed.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    advance({});
  }, [advance]);

  function submitAnswer() {
    if (!question || !selected) return;
    const next = { ...answers, [question.id]: selected };
    history.current.push(answers);
    setAnswers(next);
    setStep((s) => s + 1);
    advance(next);
  }

  function goBack() {
    if (history.current.length === 0) {
      navigate("/");
      return;
    }
    const prev = history.current.pop();
    setAnswers(prev);
    setStep((s) => Math.max(0, s - 1));
    setCategory(null);
    advance(prev);
  }

  function restart() {
    history.current = [];
    setAnswers({});
    setStep(0);
    setCategory(null);
    advance({});
  }

  // ---- completed ---------------------------------------------------------- //
  if (category) {
    return (
      <div className="classification-page">
        <div className="classification-container">
          <div className="badge">CLASSIFICATION COMPLETE</div>
          <div className="result-card">
            <p className="result-label">Likely formulation category</p>
            <h1>{CATEGORY_LABELS[category] || category}</h1>
            <p className="classification-intro">
              {CATEGORY_BLURB[category] ||
                "This is a preliminary guidance classification."}
            </p>
            <p className="result-jurisdiction">
              Jurisdiction selected:{" "}
              <strong>
                {jurisdiction === "india" ? "India" : "International"}
              </strong>
            </p>
            <div className="disclaimer">
              <strong>Important:</strong> This is a preliminary guidance
              classification, not legal or regulatory advice.
            </div>
            <div className="navigation-buttons">
              <button className="back-button" onClick={restart}>
                Start again
              </button>
              <button
                className="next-button"
                onClick={() =>
                  navigate("/ask", {
                    state: {
                      jurisdiction,
                      formulationCategory: category,
                      formulationLabel: CATEGORY_LABELS[category] || category,
                    },
                  })
                }
              >
                Continue to Ask a Question →
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ---- question / loading / error --------------------------------------- //
  return (
    <div className="classification-page">
      <div className="classification-container">
        <button className="text-back-button" onClick={goBack}>
          ← Back
        </button>

        <div className="badge">FORMULATION CLASSIFICATION</div>
        <h1>
          Let&apos;s understand your <span>formulation</span>
        </h1>
        <p className="classification-intro">
          Answer a few short questions to identify the most relevant regulatory
          and IP guidance pathway.
        </p>

        {error && (
          <div className="mismatch-card">
            <strong>Couldn&apos;t reach the classifier:</strong> {error}
            <div style={{ marginTop: "0.75rem" }}>
              <button className="back-button" onClick={() => advance(answers)}>
                Retry
              </button>
            </div>
          </div>
        )}

        {loading && !error && (
          <div className="question-card">
            <h2>Loading…</h2>
          </div>
        )}

        {question && !loading && !error && (
          <>
            <div className="progress-section">
              <div className="progress-text">Question {step + 1}</div>
            </div>
            <div className="question-card">
              <h2>{question.text}</h2>
              <div className="options">
                {question.options.map((option) => (
                  <button
                    type="button"
                    key={option}
                    className={selected === option ? "option selected" : "option"}
                    onClick={() => setSelected(option)}
                  >
                    {option}
                  </button>
                ))}
              </div>
              <div className="navigation-buttons">
                <button className="back-button" onClick={goBack}>
                  ← Back
                </button>
                <button
                  className="next-button"
                  onClick={submitAnswer}
                  disabled={!selected}
                >
                  Next →
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default Classify;
