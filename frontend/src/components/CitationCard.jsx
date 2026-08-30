import styles from "./CitationCard.module.css";

/** citation: { source, section, excerpt_ref } */
export default function CitationCard({ citation, index }) {
  const { source, section, excerpt_ref } = citation;
  const label = /^\s*(section|article)/i.test(section)
    ? section
    : `Section ${section}`;
  return (
    <article className={styles.card}>
      <span className={styles.num}>{index + 1}</span>
      <div className={styles.body}>
        <p className={styles.section}>{label}</p>
        <p className={styles.source}>{source}</p>
        {excerpt_ref && <code className={styles.ref}>{excerpt_ref}</code>}
      </div>
    </article>
  );
}
