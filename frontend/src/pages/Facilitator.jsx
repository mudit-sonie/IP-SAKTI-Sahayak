import { useCallback, useEffect, useState } from "react";
import { facilitator } from "../api/client";
import AppShell from "../components/AppShell";
import PageIntro from "../components/PageIntro";
import Button from "../components/Button";
import Badge from "../components/Badge";
import Icon from "../components/Icon";
import TextArea from "../components/TextArea";
import { SkeletonLine } from "../components/Skeleton";
import styles from "./Facilitator.module.css";

const REASON_LABEL = {
  low_retrieval: "weak retrieval",
  high_stakes: "high-stakes (FTO / infringement)",
  no_gemini: "model unavailable",
};

function QueueItem({ esc, onAnswered, onDismiss }) {
  const [open, setOpen] = useState(false);
  const [answer, setAnswer] = useState("");
  const [publish, setPublish] = useState(true);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    if (!answer.trim() || busy) return;
    setBusy(true);
    try {
      await facilitator.answerEscalation(esc.id, {
        answer: answer.trim(),
        citations: [],
        publish_faq: publish,
      });
      onAnswered();
    } finally {
      setBusy(false);
    }
  }

  return (
    <li className={styles.item}>
      <button
        type="button"
        className={styles.itemHead}
        onClick={() => setOpen((v) => !v)}
      >
        <span className={styles.q}>{esc.query}</span>
        <span className={styles.tags}>
          <Badge tone="neutral">{esc.jurisdiction}</Badge>
          <Badge tone="warn">{REASON_LABEL[esc.reason] || esc.reason}</Badge>
          {esc.source === "matter" && <Badge tone="accent">from a matter</Badge>}
        </span>
      </button>

      {open && (
        <div className={styles.itemBody}>
          {esc.context && (
            <p className={styles.context}>
              <strong>Product background:</strong> {esc.context}
            </p>
          )}
          <p className={styles.meta}>
            Queued {new Date(esc.created_at).toLocaleString()} · retrieval score{" "}
            <span className="mono">{esc.retrieval_score.toFixed(2)}</span>
          </p>
          <form onSubmit={submit}>
            <TextArea
              label="Reviewed answer"
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              rows={5}
              placeholder="Write the answer a citizen should receive…"
            />
            <label className={styles.publish}>
              <input
                type="checkbox"
                checked={publish}
                onChange={(e) => setPublish(e.target.checked)}
              />
              Publish to the reviewed FAQ (served ahead of the model on matching
              questions)
            </label>
            <div className={styles.actions}>
              <Button type="submit" size="sm" disabled={!answer.trim() || busy}>
                {busy ? "Saving…" : "Submit answer"}
              </Button>
              <button
                type="button"
                className={styles.dismiss}
                onClick={() => onDismiss(esc.id)}
              >
                Dismiss
              </button>
            </div>
          </form>
        </div>
      )}
    </li>
  );
}

export default function Facilitator() {
  const [tab, setTab] = useState("queue");
  const [queue, setQueue] = useState(null);
  const [faq, setFaq] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    setError(null);
    facilitator
      .listEscalations("open")
      .then(setQueue)
      .catch((e) => setError(e.message));
    facilitator.listFaq().then(setFaq).catch((e) => setError(e.message));
  }, []);

  useEffect(load, [load]);

  async function dismiss(id) {
    await facilitator.dismissEscalation(id);
    load();
  }
  async function removeFaq(id) {
    await facilitator.deleteFaq(id);
    load();
  }

  return (
    <AppShell width="wide">
      <PageIntro eyebrow="Facilitator" title="Escalation queue">
        Questions the assistant could not answer with confidence land here. A
        reviewed answer can be published to the FAQ, where it is served ahead of
        the model on matching questions.
      </PageIntro>

      {error && <p className={styles.error}>{error}</p>}

      <div className={styles.tabs} role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={tab === "queue"}
          className={tab === "queue" ? styles.tabOn : styles.tab}
          onClick={() => setTab("queue")}
        >
          Open queue <span className="mono">{queue?.length ?? "–"}</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "faq"}
          className={tab === "faq" ? styles.tabOn : styles.tab}
          onClick={() => setTab("faq")}
        >
          Published FAQ <span className="mono">{faq?.length ?? "–"}</span>
        </button>
      </div>

      {tab === "queue" &&
        (queue === null ? (
          <SkeletonLine w="60%" />
        ) : queue.length === 0 ? (
          <p className={styles.empty}>The queue is clear.</p>
        ) : (
          <ul className={styles.list}>
            {queue.map((esc) => (
              <QueueItem
                key={esc.id}
                esc={esc}
                onAnswered={load}
                onDismiss={dismiss}
              />
            ))}
          </ul>
        ))}

      {tab === "faq" &&
        (faq === null ? (
          <SkeletonLine w="60%" />
        ) : faq.length === 0 ? (
          <p className={styles.empty}>No reviewed answers published yet.</p>
        ) : (
          <ul className={styles.list}>
            {faq.map((f) => (
              <li key={f.id} className={styles.faqItem}>
                <div className={styles.faqHead}>
                  <span className={styles.q}>{f.question}</span>
                  <span className={styles.tags}>
                    <Badge tone="neutral">{f.jurisdiction}</Badge>
                    <button
                      type="button"
                      className={styles.dismiss}
                      onClick={() => removeFaq(f.id)}
                      aria-label="Remove FAQ entry"
                    >
                      <Icon name="close" size={13} />
                    </button>
                  </span>
                </div>
                <p className={styles.faqAnswer}>{f.answer}</p>
              </li>
            ))}
          </ul>
        ))}
    </AppShell>
  );
}
