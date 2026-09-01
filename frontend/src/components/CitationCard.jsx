import Icon from "./Icon";
import styles from "./CitationCard.module.css";

/** citation: { source, section, excerpt_ref, source_url, as_of, amended_by };
 *  onView?: () => void */
export default function CitationCard({ citation, index, onView }) {
  const { source, section, excerpt_ref, source_url, as_of, amended_by } =
    citation;
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
        {(as_of || amended_by) && (
          <span className={styles.currency}>
            {amended_by && (
              <span className={styles.amended}>
                <Icon name="alert" size={11} /> may be amended by {amended_by}
              </span>
            )}
            {as_of && <span className={styles.asOf}>text as of {as_of}</span>}
          </span>
        )}
        <span className={styles.links}>
          {clickable && (
            <span className={styles.view}>
              View passage <Icon name="arrowRight" size={13} />
            </span>
          )}
          {source_url && (
            <a
              href={source_url}
              target="_blank"
              rel="noreferrer noopener"
              className={styles.ext}
              onClick={(e) => e.stopPropagation()}
            >
              Official source <Icon name="external" size={12} />
            </a>
          )}
        </span>
      </span>
    </Tag>
  );
}
