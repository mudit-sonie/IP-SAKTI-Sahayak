import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { query as runQuery } from "../api/client";
import AppShell from "../components/AppShell";
import Button from "../components/Button";
import Badge from "../components/Badge";
import Card, { CardHeader } from "../components/Card";
import ConfidenceMeter from "../components/ConfidenceMeter";
import CitationCard from "../components/CitationCard";
import AnswerSkeleton from "../components/Skeleton";
import styles from "./Result.module.css";

export default function Result() {
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
      .then(setData)
      .catch((err) => {
        if (err.name === "AbortError") return;
        setError(err.message || "The query failed.");
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [question, jurisdiction, formulationCategory]);

  const escalated = data?.confidence?.status === "escalate";

  return (
    <AppShell context={{ jurisdiction, formulationLabel }} width="wide">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => navigate("/ask", { state: location.state })}
        className={styles.back}
      >
        ← Edit question
      </Button>

      <p className={styles.question}>{question}</p>

      {loading && <AnswerSkeleton />}

      {error && !loading && (
        <Card tone="danger">
          <CardHeader eyebrow="Request failed" title="Couldn't get an answer" />
          <p>{error}</p>
          <Button
            variant="secondary"
            className={styles.retry}
            onClick={() => navigate("/ask", { state: location.state })}
          >
            Try again
          </Button>
        </Card>
      )}

      {data && !loading && !error && (
        <div className={styles.grid}>
          <div className={styles.main}>
            <Card tone={escalated ? "warn" : "default"}>
              <CardHeader
                eyebrow={escalated ? "Escalated" : "Source-cited guidance"}
                title={
                  escalated
                    ? "Routed to a human facilitator"
                    : "Answer"
                }
                aside={
                  <Badge
                    tone={escalated ? "warn" : "accent"}
                    variant="solid"
                  >
                    {escalated ? "Escalated" : "Answered"}
                  </Badge>
                }
              />
              <p className={styles.answer}>{data.answer}</p>
              {escalated && (
                <p className={styles.escalateNote}>
                  Retrieval support or model confidence was below threshold, so
                  the assistant did not guess. A human IP facilitator can take
                  this from here.
                </p>
              )}
            </Card>

            <Card tone="muted">
              <CardHeader
                eyebrow="ABS check"
                title={
                  data.abs_flag
                    ? "Access & benefit-sharing may apply"
                    : "No ABS trigger found"
                }
                aside={
                  <Badge tone={data.abs_flag ? "warn" : "neutral"}>
                    {data.abs_flag ? "Flagged" : "Clear"}
                  </Badge>
                }
              />
              <p className={styles.absText}>
                {data.abs_flag
                  ? data.abs_note ||
                    "This query touches biological resources — a second retrieval pass over the Biological Diversity Act was run."
                  : "No biological-resource or traditional-knowledge trigger was detected in this question."}
              </p>
            </Card>
          </div>

          <aside className={styles.rail}>
            <div className={styles.railBlock}>
              <h3 className={styles.railTitle}>Confidence</h3>
              <ConfidenceMeter confidence={data.confidence} />
            </div>

            <div className={styles.railBlock}>
              <h3 className={styles.railTitle}>
                Sources{" "}
                {data.citations?.length ? `(${data.citations.length})` : ""}
              </h3>
              {data.citations?.length ? (
                <div className={styles.citations}>
                  {data.citations.map((c, i) => (
                    <CitationCard
                      key={c.excerpt_ref || `${c.source}-${c.section}-${i}`}
                      citation={c}
                      index={i}
                    />
                  ))}
                </div>
              ) : (
                <p className={styles.noCite}>
                  No passage met the citation bar — the assistant did not invent
                  one.
                </p>
              )}
            </div>
          </aside>
        </div>
      )}

      <Button
        className={styles.newQuery}
        variant="secondary"
        onClick={() => navigate("/")}
      >
        Start a new query
      </Button>
    </AppShell>
  );
}
