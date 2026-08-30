import styles from "./RetrievalDetails.module.css";

/** info: QueryResponse.retrieval */
export default function RetrievalDetails({ info }) {
  if (!info) return null;
  const {
    jurisdiction,
    expanded_query,
    passages_searched,
    sources_searched = [],
    top_sections = [],
  } = info;

  return (
    <details className={styles.wrap}>
      <summary className={styles.summary}>
        Searched {passages_searched} passages across {sources_searched.length}{" "}
        {jurisdiction === "international" ? "instruments" : "Acts"}
      </summary>
      <div className={styles.body}>
        {sources_searched.length > 0 && (
          <div className={styles.group}>
            <span className={styles.k}>Corpus</span>
            <ul className={styles.list}>
              {sources_searched.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </div>
        )}
        {expanded_query && (
          <div className={styles.group}>
            <span className={styles.k}>Query expanded to</span>
            <p className={styles.v}>{expanded_query}</p>
          </div>
        )}
        {top_sections.length > 0 && (
          <div className={styles.group}>
            <span className={styles.k}>Top-ranked sections</span>
            <ul className={styles.list}>
              {top_sections.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </details>
  );
}
