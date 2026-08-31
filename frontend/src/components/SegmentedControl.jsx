import styles from "./SegmentedControl.module.css";
import Icon from "./Icon";

const cx = (...c) => c.filter(Boolean).join(" ");

/**
 * options: [{ value, label, icon? }]
 * value: current value; onChange: (value) => void
 */
export default function SegmentedControl({
  options,
  value,
  onChange,
  ariaLabel,
}) {
  return (
    <div className={styles.group} role="radiogroup" aria-label={ariaLabel}>
      {options.map((opt) => {
        const on = value === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={on}
            className={cx(styles.opt, on && styles.on)}
            onClick={() => onChange(opt.value)}
          >
            {opt.icon && <Icon name={opt.icon} size={16} />}
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
