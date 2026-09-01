import styles from "./ClaimList.module.css";

const MARKER = /\[(\d+)\]/g;

/**
 * Renders the answer as a list of claims, each with inline footnote markers
 * ([n]) linked to the citation at that 1-based index.
 *
 * claims: [{ text, citations: number[] }]
 * citations: Citation[]  (from the same response)
 * onCite: (citation) => void  — open the passage for citation index n
 */
export default function ClaimList({ claims, citations = [], onCite }) {
  return (
    <div className={styles.list}>
      {claims.map((claim, i) => {
        const parts = [];
        let last = 0;
        let m;
        MARKER.lastIndex = 0;
        while ((m = MARKER.exec(claim.text)) !== null) {
          if (m.index > last) parts.push(claim.text.slice(last, m.index));
          const n = Number(m[1]);
          const citation = citations[n - 1];
          parts.push(
            <button
              key={`${i}-${m.index}`}
              type="button"
              className={styles.marker}
              disabled={!citation}
              onClick={citation ? () => onCite(citation) : undefined}
              aria-label={`Source ${n}`}
            >
              {n}
            </button>,
          );
          last = m.index + m[0].length;
        }
        if (last < claim.text.length) parts.push(claim.text.slice(last));

        return (
          <p
            key={i}
            className={`${styles.claim} ${
              claim.citations.length ? "" : styles.unsourced
            }`}
          >
            {parts}
          </p>
        );
      })}
    </div>
  );
}
