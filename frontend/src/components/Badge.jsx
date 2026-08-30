import styles from "./Badge.module.css";

const cx = (...c) => c.filter(Boolean).join(" ");

/** tone: "accent" | "warn" | "danger" | "neutral"; variant: "solid" | "soft" */
export default function Badge({
  tone = "accent",
  variant = "soft",
  className,
  children,
}) {
  return (
    <span className={cx(styles.badge, styles[tone], styles[variant], className)}>
      {children}
    </span>
  );
}
