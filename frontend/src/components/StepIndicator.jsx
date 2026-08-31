import Icon from "./Icon";
import styles from "./StepIndicator.module.css";

const cx = (...c) => c.filter(Boolean).join(" ");

const STEPS = ["Classify", "Question", "Answer"];

/** current: 0-based index of the active step. */
export default function StepIndicator({ current = 0 }) {
  return (
    <ol className={styles.list} aria-label="Progress">
      {STEPS.map((label, i) => {
        const state =
          i < current ? "done" : i === current ? "active" : "upcoming";
        return (
          <li key={label} className={cx(styles.step, styles[state])}>
            <span className={styles.marker} aria-hidden="true">
              {state === "done" ? <Icon name="check" size={13} /> : i + 1}
            </span>
            <span className={styles.label}>{label}</span>
          </li>
        );
      })}
    </ol>
  );
}
