import styles from "./Badge.module.css";

const cx = (...c) => c.filter(Boolean).join(" ");

/** tone: "accent" | "warn" | "danger" | "info" | "neutral"
 *  variant: "solid" | "soft" | "outline" */
export default function Badge({
  tone = "accent",
  variant = "soft",
  mono = false,
  className,
  children,
}) {
  return (
    <span
      className={cx(
        styles.badge,
        styles[tone],
        styles[variant],
        mono && styles.mono,
        className,
      )}
    >
      {children}
    </span>
  );
}
