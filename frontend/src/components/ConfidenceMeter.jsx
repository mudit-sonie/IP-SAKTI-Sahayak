import styles from "./ConfidenceMeter.module.css";

const cx = (...c) => c.filter(Boolean).join(" ");

/**
 * confidence: { retrieval_score, self_confidence, status } from POST /query.
 */
export default function ConfidenceMeter({ confidence }) {
  if (!confidence) return null;
  const { retrieval_score = 0, self_confidence, status } = confidence;
  const pct = Math.round(Math.min(1, Math.max(0, retrieval_score)) * 100);
  const answered = status === "answered";

  return (
    <div className={styles.wrap}>
      <div className={styles.row}>
        <span className={styles.label}>Retrieval match</span>
        <span className={styles.value}>{pct}%</span>
      </div>
      <div className={styles.track}>
        <div
          className={cx(styles.fill, answered ? styles.ok : styles.weak)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className={styles.meta}>
        Model self-confidence: <strong>{self_confidence}</strong>
      </p>
    </div>
  );
}
