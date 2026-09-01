import Icon from "./Icon";
import styles from "./CaseNotes.module.css";

/** notes: [{ case_name, citation, court, year, excerpt, source_url }] */
export default function CaseNotes({ notes = [] }) {
  if (!notes.length) return null;
  return (
    <ul className={styles.list}>
      {notes.map((n, i) => (
        <li key={n.chunk_id || i} className={styles.item}>
          <p className={styles.head}>
            <span className={styles.name}>{n.case_name}</span>
            {n.citation && <span className={styles.cite}>{n.citation}</span>}
          </p>
          {(n.court || n.year) && (
            <p className={styles.meta}>
              {[n.court, n.year].filter(Boolean).join(" · ")}
            </p>
          )}
          <p className={styles.excerpt}>{n.excerpt}</p>
          {n.source_url && (
            <a
              href={n.source_url}
              target="_blank"
              rel="noreferrer noopener"
              className={styles.link}
            >
              Read the decision <Icon name="external" size={12} />
            </a>
          )}
        </li>
      ))}
    </ul>
  );
}
