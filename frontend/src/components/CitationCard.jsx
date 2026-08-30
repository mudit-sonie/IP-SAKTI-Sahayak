import styles from "./CitationCard.module.css";

/** citation: { source, section, excerpt_ref, source_url }; onView?: () => void */
export default function CitationCard({ citation, index, onView }) {
  const { source, section, excerpt_ref, source_url } = citation;
  const label = /^\s*(section|article)/i.test(section)
    ? section
    : `Section ${section}`;
  const clickable = Boolean(excerpt_ref && onView);

  const Tag = clickable ? "button" : "article";
  return (
    <Tag
      className={`${styles.card} ${clickable ? styles.clickable : ""}`}
      onClick={clickable ? onView : undefined}
      type={clickable ? "button" : undefined}
    >
      <span className={styles.num}>{index + 1}</span>
      <span className={styles.body}>
        <span className={styles.section}>{label}</span>
        <span className={styles.source}>{source}</span>
        <span className={styles.links}>
          {clickable && <span className={styles.view}>View passage →</span>}
          {source_url && (
            <a
              href={source_url}
              target="_blank"
              rel="noreferrer noopener"
              className={styles.ext}
              onClick={(e) => e.stopPropagation()}
            >
              India Code ↗
            </a>
          )}
        </span>
      </span>
    </Tag>
  );
}
