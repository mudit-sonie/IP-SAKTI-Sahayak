import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { classify } from "../api/client";
import AppShell from "../components/AppShell";
import PageIntro from "../components/PageIntro";
import Button from "../components/Button";
import OptionList from "../components/OptionList";
import { SkeletonLine } from "../components/Skeleton";
import styles from "./Classify.module.css";

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

export default function Classify() {
  const navigate = useNavigate();
  const location = useLocation();
  const jurisdiction = location.state?.jurisdiction || "india";

  const [answers, setAnswers] = useState({});
  const [step, setStep] = useState(0);
  const [question, setQuestion] = useState(null);
  const [category, setCategory] = useState(null);
  const [rationale, setRationale] = useState([]);
  const [selected, setSelected] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const history = useRef([]);

  const advance = useCallback(async (nextAnswers) => {
    setLoading(true);
    setError(null);
    try {
      const res = await classify(nextAnswers);
      if (res.complete) {
        setCategory(res.formulation_category);
        setRationale(res.rationale || []);
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
      navigate("/", { state: { jurisdiction } });
      return;
    }
    const prev = history.current.pop();
    setAnswers(prev);
    setStep((s) => Math.max(0, s - 1));
    setCategory(null);
    setRationale([]);
    advance(prev);
  }

  function restart() {
    history.current = [];
    setAnswers({});
    setStep(0);
    setCategory(null);
    setRationale([]);
    advance({});
  }

  return (
    <AppShell context={{ jurisdiction }}>
      <Button variant="ghost" size="sm" onClick={goBack} className={styles.back}>
        ← Back
      </Button>

      <PageIntro eyebrow="Step 1 · Formulation classification" title="Let's place your formulation">
        A few short questions identify the most relevant regulatory and IP
        pathway. This drives which ABS and patentability rules apply later.
      </PageIntro>

      {error && (
        <div className={styles.error}>
          <p>
            <strong>Couldn&apos;t reach the classifier.</strong> {error}
          </p>
          <Button variant="secondary" size="sm" onClick={() => advance(answers)}>
            Retry
          </Button>
        </div>
      )}

      {!error && category && (
        <div className={styles.resultCard}>
          <p className={styles.resultEyebrow}>Likely category</p>
          <h2 className={styles.resultTitle}>
            {CATEGORY_LABELS[category] || category}
          </h2>
          <p className={styles.resultBlurb}>
            {CATEGORY_BLURB[category] ||
              "A preliminary guidance classification, not legal advice."}
          </p>
          {rationale.length > 0 && (
            <div className={styles.why}>
              <p className={styles.whyTitle}>Why this category</p>
              <ul className={styles.whyList}>
                {rationale.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </div>
          )}
          <div className={styles.actions}>
            <Button variant="secondary" onClick={restart}>
              Start again
            </Button>
            <Button
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
              Continue to ask a question →
            </Button>
          </div>
        </div>
      )}

      {!error && !category && (
        <div className={styles.questionCard}>
          <p className={styles.qCount}>Question {step + 1}</p>
          {loading ? (
            <div className={styles.qLoading}>
              <SkeletonLine w="70%" />
              <SkeletonLine w="100%" />
              <SkeletonLine w="100%" />
              <SkeletonLine w="55%" />
            </div>
          ) : (
            question && (
              <>
                <h2 className={styles.qText}>{question.text}</h2>
                <OptionList
                  options={question.options}
                  value={selected}
                  onChange={setSelected}
                />
                <div className={styles.actions}>
                  <Button variant="secondary" onClick={goBack}>
                    ← Back
                  </Button>
                  <Button onClick={submitAnswer} disabled={!selected}>
                    Next →
                  </Button>
                </div>
              </>
            )
          )}
        </div>
      )}
    </AppShell>
  );
}
