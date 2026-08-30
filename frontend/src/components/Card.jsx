import styles from "./Card.module.css";

const cx = (...c) => c.filter(Boolean).join(" ");

/** tone: "default" | "accent" | "warn" | "danger" | "muted" */
export default function Card({ tone = "default", className, children, ...rest }) {
  return (
    <section className={cx(styles.card, styles[tone], className)} {...rest}>
      {children}
    </section>
  );
}

export function CardHeader({ title, eyebrow, aside }) {
  return (
    <header className={styles.header}>
      <div>
        {eyebrow && <p className={styles.eyebrow}>{eyebrow}</p>}
        {title && <h2 className={styles.title}>{title}</h2>}
      </div>
      {aside}
    </header>
  );
}
