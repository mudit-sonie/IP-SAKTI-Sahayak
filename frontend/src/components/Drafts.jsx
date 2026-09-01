import Button from "./Button";
import Icon from "./Icon";
import styles from "./Drafts.module.css";

/**
 * Document drafts tab (S8).
 * kinds:   [{ kind, title, description, requires_abs }]
 * drafts:  matter.drafts [{ id, kind, title, created_at }]
 * onGenerate(kind) / onDelete(draftId) / draftUrl(draftId)
 */
export default function Drafts({
  kinds = [],
  drafts = [],
  absStatus,
  onGenerate,
  onDelete,
  draftUrl,
  busy,
}) {
  return (
    <div className={styles.wrap}>
      <p className={styles.intro}>
        Skeleton documents filled from this matter&apos;s formulation profile.
        Every legal assertion carries a section-level basis; the generated file
        lists them under &ldquo;Traceability&rdquo;. Drafts are for a
        professional to complete and verify — not filings.
      </p>

      <div className={styles.kinds}>
        {kinds.map((k) => {
          const absMissing = k.requires_abs && absStatus !== "flagged";
          return (
            <div key={k.kind} className={styles.kind}>
              <div className={styles.kindText}>
                <h4 className={styles.kindTitle}>{k.title}</h4>
                <p className={styles.kindDesc}>{k.description}</p>
                {absMissing && (
                  <p className={styles.note}>
                    Relevant once this matter&apos;s ABS status is flagged.
                  </p>
                )}
              </div>
              <Button
                size="sm"
                variant="secondary"
                disabled={busy}
                onClick={() => onGenerate(k.kind)}
              >
                Generate
              </Button>
            </div>
          );
        })}
      </div>

      {drafts.length > 0 && (
        <div className={styles.generated}>
          <h4 className={styles.genTitle}>Generated ({drafts.length})</h4>
          <ul className={styles.list}>
            {drafts
              .slice()
              .reverse()
              .map((d) => (
                <li key={d.id} className={styles.item}>
                  <span className={styles.itemMain}>
                    <span className={styles.itemName}>{d.title}</span>
                    <span className={styles.itemWhen}>
                      {new Date(d.created_at).toLocaleString()}
                    </span>
                  </span>
                  <span className={styles.actions}>
                    <a
                      className={styles.download}
                      href={draftUrl(d.id)}
                      target="_blank"
                      rel="noreferrer noopener"
                    >
                      <Icon name="external" size={12} /> Download (.md)
                    </a>
                    <button
                      type="button"
                      className={styles.remove}
                      onClick={() => onDelete(d.id)}
                    >
                      Remove
                    </button>
                  </span>
                </li>
              ))}
          </ul>
        </div>
      )}
    </div>
  );
}
