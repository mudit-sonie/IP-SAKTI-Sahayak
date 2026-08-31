import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import PageIntro from "../components/PageIntro";
import Button from "../components/Button";
import TextArea from "../components/TextArea";
import Icon from "../components/Icon";
import styles from "./Ask.module.css";

const EXAMPLES = [
  "Can a classical Ayurvedic formulation be patented in India?",
  "Do I need NBA approval before filing a patent that uses a biological resource?",
  "What is the term of a patent in India?",
];

export default function Ask() {
  const navigate = useNavigate();
  const location = useLocation();

  const jurisdiction = location.state?.jurisdiction || "india";
  const formulationCategory = location.state?.formulationCategory || null;
  const formulationLabel =
    location.state?.formulationLabel || formulationCategory || "Not classified";

  const [query, setQuery] = useState("");

  function handleSubmit(event) {
    event.preventDefault();
    const clean = query.trim();
    if (!clean) return;
    navigate("/result", {
      state: {
        jurisdiction,
        formulationCategory,
        formulationLabel,
        query: clean,
      },
    });
  }

  return (
    <AppShell context={{ jurisdiction, formulationLabel }}>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => navigate("/classify", { state: { jurisdiction } })}
        className={styles.back}
      >
        <Icon name="arrowLeft" size={14} />
        Back to classification
      </Button>

      <PageIntro
        eyebrow="Step 2 / 3 · Your question"
        title="Ask an IP or regulatory question"
      >
        You&apos;ll get source-cited guidance grounded in the {formulationLabel}{" "}
        pathway and your selected jurisdiction.
      </PageIntro>

      <form className={styles.form} onSubmit={handleSubmit}>
        <TextArea
          label="Your question"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. Can I patent this formulation in India?"
          rows={5}
        />

        <div className={styles.examples}>
          <p className={styles.exLabel}>Try one of these</p>
          <ul className={styles.exList}>
            {EXAMPLES.map((ex) => (
              <li key={ex}>
                <button
                  type="button"
                  className={styles.example}
                  onClick={() => setQuery(ex)}
                >
                  {ex}
                </button>
              </li>
            ))}
          </ul>
        </div>

        <Button type="submit" className={styles.submit} disabled={!query.trim()}>
          Get source-cited guidance
          <Icon name="arrowRight" size={16} />
        </Button>
      </form>
    </AppShell>
  );
}
