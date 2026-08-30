import { useState } from "react";
import { sendFeedback } from "../api/client";
import Button from "./Button";
import styles from "./FeedbackWidget.module.css";

/** meta: { query, jurisdiction, formulationCategory, answerStatus, citedSections } */
export default function FeedbackWidget({ meta }) {
  const [rating, setRating] = useState(null); // "up" | "down"
  const [note, setNote] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(value, withNote) {
    setBusy(true);
    try {
      await sendFeedback({
        query: meta.query,
        rating: value,
        note: withNote ? note : undefined,
        jurisdiction: meta.jurisdiction,
        formulation_category: meta.formulationCategory || undefined,
        answer_status: meta.answerStatus,
        cited_sections: meta.citedSections || [],
      });
      setDone(true);
    } catch {
      setDone(true); // fire-and-forget; never block the user on feedback
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return <p className={styles.thanks}>Thanks — logged for review.</p>;
  }

  return (
    <div className={styles.wrap}>
      <span className={styles.label}>Was this useful?</span>
      <button
        type="button"
        className={`${styles.thumb} ${rating === "up" ? styles.on : ""}`}
        aria-pressed={rating === "up"}
        disabled={busy}
        onClick={() => {
          setRating("up");
          submit("up", false);
        }}
      >
        👍
      </button>
      <button
        type="button"
        className={`${styles.thumb} ${rating === "down" ? styles.on : ""}`}
        aria-pressed={rating === "down"}
        disabled={busy}
        onClick={() => setRating("down")}
      >
        👎
      </button>

      {rating === "down" && (
        <form
          className={styles.noteRow}
          onSubmit={(e) => {
            e.preventDefault();
            submit("down", true);
          }}
        >
          <input
            className={styles.note}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="What was wrong? (optional)"
            autoFocus
          />
          <Button type="submit" size="sm" disabled={busy}>
            Send
          </Button>
        </form>
      )}
    </div>
  );
}
