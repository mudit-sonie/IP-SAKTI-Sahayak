import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { matters as mattersApi } from "../api/client";
import AppShell from "../components/AppShell";
import Button from "../components/Button";
import Badge from "../components/Badge";
import Icon from "../components/Icon";
import CitationCard from "../components/CitationCard";
import ConfidenceMeter from "../components/ConfidenceMeter";
import PassageDrawer from "../components/PassageDrawer";
import TextArea from "../components/TextArea";
import AnswerSkeleton from "../components/Skeleton";
import styles from "./Matter.module.css";

const ABS_TONE = { flagged: "warn", clear: "accent", unknown: "neutral" };

export default function Matter() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [matter, setMatter] = useState(null);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState("");
  const [asking, setAsking] = useState(false);
  const [viewing, setViewing] = useState(null);
  const [notes, setNotes] = useState("");
  const notesDirty = useRef(false);

  const load = useCallback(
    (signal) =>
      mattersApi
        .get(id, { signal })
        .then((m) => {
          setMatter(m);
          if (!notesDirty.current) setNotes(m.notes || "");
        })
        .catch((err) => {
          if (err.name !== "AbortError") setError(err.message);
        }),
    [id],
  );

  useEffect(() => {
    const ac = new AbortController();
    load(ac.signal);
    return () => ac.abort();
  }, [load]);

  async function ask(e) {
    e.preventDefault();
    const clean = query.trim();
    if (!clean || asking) return;
    setAsking(true);
    setError(null);
    try {
      const res = await mattersApi.ask(id, { query: clean });
      setMatter(res.matter);
      setQuery("");
    } catch (err) {
      setError(err.message);
    } finally {
      setAsking(false);
    }
  }

  async function saveNotes() {
    try {
      const m = await mattersApi.update(id, { notes });
      notesDirty.current = false;
      setMatter(m);
    } catch (err) {
      setError(err.message);
    }
  }

  async function remove() {
    if (!window.confirm("Delete this matter and its history?")) return;
    await mattersApi.remove(id);
    navigate("/matters");
  }

  if (error && !matter) {
    return (
      <AppShell>
        <p className={styles.error}>{error}</p>
        <Link to="/matters">← Back to matters</Link>
      </AppShell>
    );
  }
  if (!matter) {
    return (
      <AppShell>
        <p className={styles.loading}>Loading matter…</p>
      </AppShell>
    );
  }

  const questions = [...matter.questions].reverse();

  return (
    <AppShell
      context={{
        jurisdiction: matter.jurisdiction,
        formulationLabel: matter.formulation_label || undefined,
      }}
      width="wide"
    >
      <Button
        variant="ghost"
        size="sm"
        onClick={() => navigate("/matters")}
        className={styles.back}
      >
        <Icon name="arrowLeft" size={14} />
        All matters
      </Button>

      <header className={styles.head}>
        <div>
          <h1 className={styles.title}>{matter.title}</h1>
          <p className={styles.sub}>
            <Icon
              name={matter.jurisdiction === "international" ? "globe" : "india"}
              size={13}
            />
            {matter.jurisdiction === "international" ? "International" : "India"}
            <span className={styles.dot}>·</span>
            {matter.formulation_label || "Not classified"}
          </p>
        </div>
        <div className={styles.headActions}>
          <Badge tone={ABS_TONE[matter.abs_status]} variant="soft">
            ABS: {matter.abs_status}
          </Badge>
          <button className={styles.delete} onClick={remove} type="button">
            Delete
          </button>
        </div>
      </header>

      <div className={styles.grid}>
        <div className={styles.main}>
          <form className={styles.askBox} onSubmit={ask}>
            <TextArea
              label="Ask a question about this formulation"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. Can we claim this as a proprietary Ayurvedic medicine?"
              rows={3}
            />
            <Button type="submit" disabled={!query.trim() || asking}>
              {asking ? "Grounding…" : "Ask"}
              {!asking && <Icon name="arrowRight" size={16} />}
            </Button>
          </form>

          {error && <p className={styles.error}>{error}</p>}
          {asking && <AnswerSkeleton />}

          {questions.length === 0 && !asking && (
            <p className={styles.empty}>
              No questions yet. Every answer here is grounded in the corpus and
              frozen into the matter&apos;s record.
            </p>
          )}

          {questions.map((q) => {
            const escalated = q.status === "escalate";
            return (
              <article key={q.id} className={styles.qa}>
                <p className={styles.q}>{q.query}</p>
                <div className={styles.badges}>
                  <Badge
                    tone={escalated ? "warn" : "accent"}
                    variant="solid"
                  >
                    {escalated ? "Escalated" : "Answered"}
                  </Badge>
                  {q.abs_flag && <Badge tone="warn">ABS flagged</Badge>}
                  <span className={styles.asked}>
                    {new Date(q.asked_at).toLocaleDateString()}
                  </span>
                </div>
                <p className={styles.a}>{q.answer}</p>
                {q.citations.length > 0 && (
                  <div className={styles.cites}>
                    {q.citations.map((c, i) => (
                      <CitationCard
                        key={c.excerpt_ref || `${c.source}-${c.section}-${i}`}
                        citation={c}
                        index={i}
                        onView={() => setViewing(c)}
                      />
                    ))}
                  </div>
                )}
              </article>
            );
          })}
        </div>

        <aside className={styles.rail}>
          <section className={styles.railBlock}>
            <h2 className={styles.railTitle}>Confidence — latest</h2>
            {questions[0] ? (
              <ConfidenceMeter
                confidence={{
                  retrieval_score: questions[0].retrieval_score,
                  self_confidence: questions[0].self_confidence,
                  status: questions[0].status,
                }}
              />
            ) : (
              <p className={styles.railMuted}>Ask a question to see this.</p>
            )}
          </section>

          {matter.classification_rationale.length > 0 && (
            <section className={styles.railBlock}>
              <h2 className={styles.railTitle}>Classification path</h2>
              <ul className={styles.rationale}>
                {matter.classification_rationale.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </section>
          )}

          <section className={styles.railBlock}>
            <h2 className={styles.railTitle}>Notes</h2>
            <TextArea
              value={notes}
              onChange={(e) => {
                notesDirty.current = true;
                setNotes(e.target.value);
              }}
              placeholder="Working notes for this matter…"
              rows={4}
            />
            {notesDirty.current && (
              <Button size="sm" variant="secondary" onClick={saveNotes}>
                Save notes
              </Button>
            )}
          </section>
        </aside>
      </div>

      <PassageDrawer citation={viewing} onClose={() => setViewing(null)} />
    </AppShell>
  );
}
