import styles from "./Button.module.css";

const cx = (...c) => c.filter(Boolean).join(" ");

/** variant: "primary" | "secondary" | "ghost"; size: "md" | "sm" */
export default function Button({
  variant = "primary",
  size = "md",
  as,
  className,
  ...props
}) {
  const Tag = as || "button";
  return (
    <Tag
      className={cx(styles.btn, styles[variant], styles[size], className)}
      {...props}
    />
  );
}
