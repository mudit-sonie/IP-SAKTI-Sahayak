import styles from "./OptionList.module.css";
import useSpotlight from "../hooks/useSpotlight";

const cx = (...c) => c.filter(Boolean).join(" ");

function Option({ option, value, onChange, name }) {
  const selected = value === option;
  const spotlight = useSpotlight();
  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      name={name}
      ref={spotlight.ref}
      onMouseMove={spotlight.onMouseMove}
      onMouseLeave={spotlight.onMouseLeave}
      className={cx(styles.option, selected && styles.selected, "spotlight")}
      onClick={() => onChange(option)}
    >
      <span className={styles.dot} aria-hidden="true" />
      <span>{option}</span>
    </button>
  );
}

/** options: string[]; value: string; onChange: (option) => void */
export default function OptionList({ options, value, onChange, name = "opt" }) {
  return (
    <div className={styles.list} role="radiogroup">
      {options.map((option) => (
        <Option
          key={option}
          option={option}
          value={value}
          onChange={onChange}
          name={name}
        />
      ))}
    </div>
  );
}
