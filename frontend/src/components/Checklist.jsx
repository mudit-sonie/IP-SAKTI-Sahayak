import Icon from "./Icon";
import styles from "./Checklist.module.css";

const cx = (...c) => c.filter(Boolean).join(" ");

const NEXT = {
  todo: "in_progress",
  in_progress: "done",
  done: "not_applicable",
  not_applicable: "todo",
};
const LABEL = {
  todo: "To do",
  in_progress: "In progress",
  done: "Done",
  not_applicable: "N/A",
};

function StatusButton({ status, onChange, disabled }) {
  return (
    <button
      type="button"
      className={cx(styles.status, styles[status])}
      onClick={() => onChange(NEXT[status])}
      disabled={disabled}
      aria-label={`Status: ${LABEL[status]}. Click to change.`}
      title={`${LABEL[status]} — click to advance`}
    >
      {status === "done" && <Icon name="check" size={13} />}
      {status === "not_applicable" && <Icon name="close" size={12} />}
      <span>{LABEL[status]}</span>
    </button>
  );
}

/**
 * items: ChecklistItem[]
 * onSetStatus(itemId, status); onView(citation); onRegenerate(); busy
 */
export default function Checklist({ items, onSetStatus, onView, onRegenerate, busy }) {
  const groups = items.reduce((acc, item) => {
    const g = item.group || "Other";
    (acc[g] ||= []).push(item);
    return acc;
  }, {});
  const done = items.filter((i) => i.status === "done").length;
  const active = items.filter((i) => i.status !== "not_applicable").length;

  return (
    <div className={styles.wrap}>
      <div className={styles.head}>
        <p className={styles.progress}>
          <span className="mono">
            {done}/{active}
          </span>{" "}
          complete
        </p>
        <button
          type="button"
          className={styles.regen}
          onClick={onRegenerate}
          disabled={busy}
        >
          {busy ? "Regenerating…" : "Regenerate"}
        </button>
      </div>

      {items.length === 0 && (
        <p className={styles.empty}>
          No checklist yet — it&apos;s generated from the formulation category,
          jurisdiction, and ABS status. Classify the matter first.
        </p>
      )}

      {Object.entries(groups).map(([group, groupItems]) => (
        <section key={group} className={styles.group}>
          <h3 className={styles.groupTitle}>{group}</h3>
          <ul className={styles.list}>
            {groupItems.map((item) => (
              <li
                key={item.id}
                className={cx(
                  styles.item,
                  item.status === "done" && styles.itemDone,
                  item.status === "not_applicable" && styles.itemNa,
                )}
              >
                <StatusButton
                  status={item.status}
                  disabled={busy}
                  onChange={(s) => onSetStatus(item.id, s)}
                />
                <div className={styles.body}>
                  <p className={styles.title}>{item.title}</p>
                  {item.detail && <p className={styles.detail}>{item.detail}</p>}
                  {item.citations?.length > 0 && (
                    <button
                      type="button"
                      className={styles.cite}
                      onClick={() => onView(item.citations[0])}
                    >
                      <span className="mono">
                        {item.citations[0].source} § {item.citations[0].section}
                      </span>
                      <Icon name="arrowRight" size={12} />
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
