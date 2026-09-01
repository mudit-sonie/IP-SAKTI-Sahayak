import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { compare as runCompare } from "../api/client";
import AppShell from "../components/AppShell";
import Button from "../components/Button";
import Badge from "../components/Badge";
import Icon from "../components/Icon";
import ConfidenceMeter from "../components/ConfidenceMeter";
import ClaimList from "../components/ClaimList";
import CitationCard from "../components/CitationCard";
import PassageDrawer from "../components/PassageDrawer";
import AnswerSkeleton from "../components/Skeleton";
import styles from "./Compare.module.css";

function Column({ label, icon, data, onView }) {
  const escalated = data.confidence?.status === "escalate";
  return (
    <section className={styles.col}>
      <header className={styles.colHead}>
        <Badge tone="accent">
          <Icon name={icon} size={13} /> {label}
        </Badge>
        <Badge tone={escalated ? "warn" : "accent"} variant="solid">
          {escalated ? "Escalated" : "Answered"}
        </Badge>
      </header>

      <ConfidenceMeter confidence={data.confidence} />

      {!escalated && data.claims?.length ? (
        <ClaimList
          claims={data.claims}
          citations={data.citations}
          onCite={onView}
        />
      ) : (
        <p className={styles.answer}>{data.answer}</p>
      )}

      {data.abs_flag && (
        <p className={styles.abs}>
          <Icon name="alert" size={12} /> ABS may apply —{" "}
          {data.abs_note || "biological-resource trigger detected."}
        </p>
      )}

      {data.citations?.length > 0 && (
        <div className={styles.cites}>
          <h3 className={styles.citesTitle}>
            Sources <span className="mono">({data.citations.length})</span>
          </h3>
          {data.citations.map((c, i) => (
            <CitationCard
              key={c.excerpt_ref || `${c.source}-${c.section}-${i}`}
              citation={c}
              index={i}
              onView={() => onView(c)}
            />
          ))}
        </div>
      )}
    </section>
  );
}

export default function Compare() {
  const navigate = useNavigate();
  const location = useLocation();
  const question = location.state?.query || "";
  const formulationCategory = location.state?.formulationCategory || null;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(Boolean(question));
  const [error, setError] = useState(null);
  const [viewing, setViewing] = useState(null);

  useEffect(() => {
    if (!question) return;
    const ac = new AbortController();
    setLoading(true);
    setError(null);
    runCompare({ query: question, formulationCategory }, { signal: ac.signal })
      .then(setData)
      .catch((err) => {
        if (err.name !== "AbortError") setError(err.message || "Comparison failed.");
      })
      .finally(() => setLoading(false));
    return () => ac.abort();
  }, [question, formulationCategory]);

  return (
    <AppShell width="wide">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => navigate(-1)}
        className={styles.back}
      >
        <Icon name="arrowLeft" size={14} />
        Back
      </Button>

      <h1 className={styles.title}>Compare jurisdictions</h1>

      {!question && (
        <p className={styles.hint}>
          Open this from an answer to see the India and International positions
          side by side.
        </p>
      )}

      {question && <p className={styles.question}>{question}</p>}

      {loading && (
        <div className={styles.grid}>
          <AnswerSkeleton />
          <AnswerSkeleton />
        </div>
      )}

      {error && !loading && <p className={styles.error}>{error}</p>}

      {data && !loading && (
        <div className={styles.grid}>
          <Column
            label="India"
            icon="india"
            data={data.india}
            onView={setViewing}
          />
          <Column
            label="International"
            icon="globe"
            data={data.international}
            onView={setViewing}
          />
        </div>
      )}

      <PassageDrawer citation={viewing} onClose={() => setViewing(null)} />
    </AppShell>
  );
}
