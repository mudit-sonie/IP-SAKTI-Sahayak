import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { matters as mattersApi, getStateRules, BASE_URL } from "../api/client";
import AppShell from "../components/AppShell";
import Button from "../components/Button";
import Badge from "../components/Badge";
import Icon from "../components/Icon";
import CitationCard from "../components/CitationCard";
import Checklist from "../components/Checklist";
import Drafts from "../components/Drafts";
import Deadlines from "../components/Deadlines";
import MatterDocuments from "../components/MatterDocuments";
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
  const [draftKinds, setDraftKinds] = useState([]);
  const [draftBusy, setDraftBusy] = useState(false);
  const [stateRules, setStateRules] = useState(null);

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

  useEffect(() => {
    const ac = new AbortController();
    mattersApi
      .draftKinds({ signal: ac.signal })
      .then(setDraftKinds)
      .catch(() => {});
    getStateRules({ signal: ac.signal })
      .then(setStateRules)
      .catch(() => {});
    return () => ac.abort();
  }, []);

  async function setMatterState(state) {
    try {
      setMatter(await mattersApi.update(id, { state: state || null }));
    } catch (err) {
      setError(err.message);
    }
  }

  async function generateDraft(kind) {
    setDraftBusy(true);
    setError(null);
    try {
      setMatter(await mattersApi.createDraft(id, kind));
    } catch (err) {
      setError(err.message);
    } finally {
      setDraftBusy(false);
    }
  }

  async function deleteDraft(draftId) {
    try {
      setMatter(await mattersApi.deleteDraft(id, draftId));
    } catch (err) {
      setError(err.message);
    }
  }

  const runDeadline = (fn) => async (...args) => {
    try {
      setMatter(await fn(...args));
    } catch (err) {
      setError(err.message);
    }
  };
  const deriveDeadlines = runDeadline((anchor, date) =>
    mattersApi.deriveDeadlines(id, anchor, date),
  );
  const addDeadline = runDeadline((payload) =>
    mattersApi.addDeadline(id, payload),
  );
  const toggleDeadline = runDeadline((dlId, done) =>
    mattersApi.setDeadlineDone(id, dlId, done),
  );
  const deleteDeadline = runDeadline((dlId) =>
    mattersApi.deleteDeadline(id, dlId),
  );

  async function uploadDoc(payload) {
    setMatter(await mattersApi.uploadDocument(id, payload));
  }
  async function deleteDoc(docId) {
    try {
      setMatter(await mattersApi.deleteDocument(id, docId));
    } catch (err) {
      setError(err.message);
    }
  }

  async function runTkdl() {
    try {
      setMatter(await mattersApi.tkdlCheck(id));
    } catch (err) {
      setError(err.message);
    }
  }

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
              aria-selected={tab === "deadlines"}
              className={tab === "deadlines" ? styles.tabOn : styles.tab}
              onClick={() => setTab("deadlines")}
            >
              Deadlines{" "}
              <span className="mono">
                {matter.deadlines.filter((d) => !d.done).length}
              </span>
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={tab === "documents"}
              className={tab === "documents" ? styles.tabOn : styles.tab}
              onClick={() => setTab("documents")}
            >
              Drafts <span className="mono">{matter.drafts.length}</span>
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={tab === "attachments"}
              className={tab === "attachments" ? styles.tabOn : styles.tab}
              onClick={() => setTab("attachments")}
            >
              Attachments{" "}
              <span className="mono">{matter.documents?.length || 0}</span>
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

          {tab === "deadlines" && (
            <Deadlines
              deadlines={matter.deadlines}
              anchorDates={matter.anchor_dates || {}}
              onDerive={deriveDeadlines}
              onAdd={addDeadline}
              onToggle={toggleDeadline}
              onDelete={deleteDeadline}
              onView={setViewing}
            />
          )}

          {tab === "attachments" && (
            <MatterDocuments
              documents={matter.documents || []}
              onUpload={uploadDoc}
              onDelete={deleteDoc}
            />
          )}

          {tab === "documents" && (
            <Drafts
              kinds={draftKinds}
              drafts={matter.drafts}
              absStatus={matter.abs_status}
              onGenerate={generateDraft}
              onDelete={deleteDraft}
              draftUrl={(draftId) => mattersApi.draftUrl(id, draftId)}
              busy={draftBusy}
            />
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
                {q.doc_context?.length > 0 && (
                  <div className={styles.docStrip}>
                    <p className={styles.docStripHead}>
                      Grounded partly in your documents (background, not cited)
                    </p>
                    {q.doc_context.map((s, di) => (
                      <p key={di} className={styles.docSnip}>
                        <span className={styles.docLoc}>{s.locator}</span>
                        {s.text}
                      </p>
                    ))}
                  </div>
                )}
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

          <section className={styles.railBlock}>
            <h2 className={styles.railTitle}>State &amp; ASU&amp;H licensing</h2>
            <select
              className={styles.stateSelect}
              value={matter.state || ""}
              onChange={(e) => setMatterState(e.target.value)}
              disabled={!stateRules}
            >
              <option value="">Select state (optional)…</option>
              {stateRules?.authorities.map((a) => (
                <option key={a.key} value={a.key}>
                  {a.state}
                </option>
              ))}
            </select>
            {matter.state &&
              stateRules?.authorities
                .filter((a) => a.key === matter.state)
                .map((a) => (
                  <div key={a.key} className={styles.stateAuth}>
                    <p className={styles.stateAuthName}>{a.authority}</p>
                    {a.portal_url && (
                      <a
                        href={a.portal_url}
                        target="_blank"
                        rel="noreferrer noopener"
                        className={styles.stateAuthLink}
                      >
                        Licensing portal{" "}
                        <Icon name="external" size={11} />
                      </a>
                    )}
                    <p className={styles.tkdlNote}>{stateRules.note}</p>
                  </div>
                ))}
          </section>

          <section className={styles.railBlock}>
            <h2 className={styles.railTitle}>TKDL prior-art check</h2>
            {matter.tkdl ? (
              <div className={styles.tkdl}>
                <Badge tone="neutral">
                  {matter.tkdl.status === "not_connected"
                    ? "Not connected"
                    : matter.tkdl.status}
                </Badge>
                <p className={styles.tkdlNote}>{matter.tkdl.note}</p>
                {matter.tkdl.search_terms.length > 0 && (
                  <p className={styles.tkdlTerms}>
                    Search terms:{" "}
                    {matter.tkdl.search_terms.map((t) => (
                      <span key={t} className={styles.tkdlTerm}>
                        {t}
                      </span>
                    ))}
                  </p>
                )}
                <Button size="sm" variant="ghost" onClick={runTkdl}>
                  Re-run
                </Button>
              </div>
            ) : (
              <div className={styles.tkdl}>
                <p className={styles.railMuted}>
                  Cross-check the formulation against the Traditional Knowledge
                  Digital Library. The TKDL is access-controlled — this assembles
                  the search terms and is honest that no connector is wired.
                </p>
                <Button size="sm" variant="secondary" onClick={runTkdl}>
                  Run TKDL check
                </Button>
              </div>
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
