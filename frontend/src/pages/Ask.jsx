import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import PageIntro from "../components/PageIntro";
import Button from "../components/Button";
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
        ← Back to classification
      </Button>

      <PageIntro eyebrow="Step 2 · Your question" title="Ask an IP or regulatory question">
        You&apos;ll get source-cited guidance grounded in the {formulationLabel}{" "}
        pathway and your selected jurisdiction.
      </PageIntro>

      <form className={styles.card} onSubmit={handleSubmit}>
        <label htmlFor="query" className={styles.label}>
          Your question
        </label>
        <textarea
          id="query"
          className={styles.textarea}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. Can I patent this formulation in India?"
          rows={5}
        />

        <p className={styles.exLabel}>Examples</p>
        <div className={styles.examples}>
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              type="button"
              className={styles.example}
              onClick={() => setQuery(ex)}
            >
              {ex}
            </button>
          ))}
        </div>

        <Button type="submit" className={styles.submit} disabled={!query.trim()}>
          Get source-cited guidance →
        </Button>
      </form>
    </AppShell>
  );
}
