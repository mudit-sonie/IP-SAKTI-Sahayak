import { useId } from "react";
import styles from "./TextArea.module.css";

/**
 * Labelled textarea with an optional hint. Extra props pass through to the
 * underlying <textarea> (value, onChange, rows, placeholder, …).
 */
export default function TextArea({ label, hint, id, ...props }) {
  const auto = useId();
  const fieldId = id || auto;
  return (
    <div className={styles.field}>
      {label && (
        <label htmlFor={fieldId} className={styles.label}>
          {label}
        </label>
      )}
      <textarea id={fieldId} className={styles.input} {...props} />
      {hint && <p className={styles.hint}>{hint}</p>}
    </div>
  );
}
