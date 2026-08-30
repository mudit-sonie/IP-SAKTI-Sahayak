import styles from "./PageIntro.module.css";

export default function PageIntro({ eyebrow, title, children }) {
  return (
    <div className={styles.intro}>
      {eyebrow && <p className={styles.eyebrow}>{eyebrow}</p>}
      <h1 className={styles.title}>{title}</h1>
      {children && <p className={styles.sub}>{children}</p>}
    </div>
  );
}
