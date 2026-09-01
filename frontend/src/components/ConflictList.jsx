import styles from "./ConflictList.module.css";

/**
 * Divergent positions across retrieved instruments.
 * conflicts: [{ topic, positions: [{ summary, citations: number[] }] }]
 * citations: Citation[] from the same response
 * onCite: (citation) => void
 */
export default function ConflictList({ conflicts, citations = [], onCite }) {
  return (
    <div className={styles.list}>
      {conflicts.map((conflict, i) => (
        <div key={i} className={styles.conflict}>
          <p className={styles.topic}>{conflict.topic}</p>
          <ul className={styles.positions}>
            {conflict.positions.map((pos, j) => (
              <li key={j} className={styles.position}>
                <span className={styles.summary}>{pos.summary}</span>
                <span className={styles.markers}>
                  {pos.citations.map((n) => {
                    const citation = citations[n - 1];
                    return (
                      <button
                        key={n}
                        type="button"
                        className={styles.marker}
                        disabled={!citation}
                        onClick={citation ? () => onCite(citation) : undefined}
                      >
                        {citation
                          ? `${citation.source} §${citation.section}`
                          : `Source ${n}`}
                      </button>
                    );
                  })}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
