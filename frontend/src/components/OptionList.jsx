import styles from "./OptionList.module.css";

const cx = (...c) => c.filter(Boolean).join(" ");

/** options: string[]; value: string; onChange: (option) => void */
export default function OptionList({ options, value, onChange, name = "opt" }) {
  return (
    <div className={styles.list} role="radiogroup">
      {options.map((option) => {
        const selected = value === option;
        return (
          <button
            type="button"
            key={option}
            role="radio"
            aria-checked={selected}
            name={name}
            className={cx(styles.option, selected && styles.selected)}
            onClick={() => onChange(option)}
          >
            <span className={styles.dot} aria-hidden="true" />
            <span>{option}</span>
          </button>
        );
      })}
    </div>
  );
}
