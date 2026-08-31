import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { matters as mattersApi, BASE_URL } from "../api/client";
import AppShell from "../components/AppShell";
import Button from "../components/Button";
import Badge from "../components/Badge";
import Icon from "../components/Icon";
import CitationCard from "../components/CitationCard";
import Checklist from "../components/Checklist";
import ConfidenceMeter from "../components/ConfidenceMeter";
import PassageDrawer from "../components/PassageDrawer";
import TextArea from "../components/TextArea";
import FormulationProfile from "../components/FormulationProfile";
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
  const [tab, setTab] = useState("questions");
  const [checklistBusy, setChecklistBusy] = useState(false);

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

  async function regenerateChecklist() {
    setChecklistBusy(true);
    try {
      setMatter(await mattersApi.regenerateChecklist(id));
    } catch (err) {
      setError(err.message);
    } finally {
      setChecklistBusy(false);
    }
  }

  async function setChecklistStatus(itemId, status) {
    setMatter(await mattersApi.setChecklistStatus(id, itemId, status));
  }

  async function saveProfile(profile) {
    setMatter(await mattersApi.update(id, { profile }));
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

      {!matter.formulation_category && (
        <div className={styles.classifyBanner}>
          <div>
            <strong>This matter isn&apos;t classified.</strong> Classifying it
            picks the right compliance rules and sharpens every answer.
          </div>
          <Button
            size="sm"
            onClick={() =>
              navigate(`/classify?matter=${matter.id}`, {
                state: { jurisdiction: matter.jurisdiction },
              })
            }
          >
            Classify this formulation
            <Icon name="arrowRight" size={14} />
          </Button>
        </div>
      )}

      <div className={styles.grid}>
        <div className={styles.main}>
          <div className={styles.tabs} role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={tab === "questions"}
              className={tab === "questions" ? styles.tabOn : styles.tab}
              onClick={() => setTab("questions")}
            >
              Questions{" "}
              <span className="mono">{matter.questions.length}</span>
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={tab === "checklist"}
              className={tab === "checklist" ? styles.tabOn : styles.tab}
              onClick={() => setTab("checklist")}
            >
              Compliance checklist{" "}
              <span className="mono">
                {matter.checklist.filter((c) => c.status !== "done").length}
              </span>
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={tab === "activity"}
              className={tab === "activity" ? styles.tabOn : styles.tab}
              onClick={() => setTab("activity")}
            >
              Activity
            </button>
          </div>

          {tab === "activity" && (
            <ol className={styles.audit}>
              {[...matter.audit].reverse().map((a, i) => (
                <li key={i} className={styles.auditItem}>
                  <span className={styles.auditWhen}>
                    {new Date(a.at).toLocaleString()}
                  </span>
                  <span className={styles.auditWhat}>
                    <span className="mono">{a.action}</span>
                    {a.detail ? ` — ${a.detail}` : ""}
                  </span>
                </li>
              ))}
            </ol>
          )}

          {tab === "checklist" && (
            <Checklist
              items={matter.checklist}
              onSetStatus={setChecklistStatus}
              onView={setViewing}
              onRegenerate={regenerateChecklist}
              busy={checklistBusy}
            />
          )}

          {tab === "questions" && (
            <>
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
                <a
                  className={styles.export}
                  href={`${BASE_URL}/matters/${id}/questions/${q.id}/export`}
                  target="_blank"
                  rel="noreferrer noopener"
                >
                  <Icon name="external" size={12} />
                  Export for records (.md)
                </a>
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
            </>
          )}
        </div>

        <aside className={styles.rail}>
          <section className={styles.railBlock}>
            <h2 className={styles.railTitle}>Formulation profile</h2>
            <FormulationProfile
              profile={matter.profile || {}}
              onSave={saveProfile}
            />
          </section>

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
