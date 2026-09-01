import { useState } from "react";
import Button from "./Button";
import Badge from "./Badge";
import Icon from "./Icon";
import CitationCard from "./CitationCard";
import styles from "./Deadlines.module.css";

const ANCHORS = [
  { value: "patent_filing", label: "Patent filing date" },
  { value: "patent_priority", label: "Patent priority date" },
  { value: "tm_application", label: "Trade mark application date" },
  { value: "gi_application", label: "GI application date" },
];

const DAY = 86_400_000;

function urgency(due, done) {
  if (done) return null;
  const days = Math.ceil((new Date(due).getTime() - Date.now()) / DAY);
  if (days < 0) return { tone: "warn", text: `overdue by ${-days}d` };
  if (days <= 30) return { tone: "warn", text: `due in ${days}d` };
  if (days <= 90) return { tone: "neutral", text: `due in ${days}d` };
  return null;
}

export default function Deadlines({
  deadlines = [],
  anchorDates = {},
  onDerive,
  onAdd,
  onToggle,
  onDelete,
  onView,
  busy,
}) {
  const [anchor, setAnchor] = useState("patent_filing");
  const [anchorDate, setAnchorDate] = useState("");
  const [title, setTitle] = useState("");
  const [due, setDue] = useState("");

  const sorted = [...deadlines].sort((a, b) =>
    a.due_date < b.due_date ? -1 : a.due_date > b.due_date ? 1 : 0,
  );

  return (
    <div className={styles.wrap}>
      <div className={styles.tools}>
        <form
          className={styles.tool}
          onSubmit={(e) => {
            e.preventDefault();
            if (anchorDate) onDerive(anchor, anchorDate);
          }}
        >
          <p className={styles.toolLabel}>Derive statutory deadlines</p>
          <div className={styles.row}>
            <select
              className={styles.select}
              value={anchor}
              onChange={(e) => setAnchor(e.target.value)}
            >
              {ANCHORS.map((a) => (
                <option key={a.value} value={a.value}>
                  {a.label}
                </option>
              ))}
            </select>
            <input
              type="date"
              className={styles.input}
              value={anchorDate}
              onChange={(e) => setAnchorDate(e.target.value)}
              aria-label="Anchor date"
            />
            <Button size="sm" type="submit" disabled={!anchorDate || busy}>
              Derive
            </Button>
          </div>
          {Object.keys(anchorDates).length > 0 && (
            <p className={styles.hint}>
              Set:{" "}
              {Object.entries(anchorDates)
                .map(([k, v]) => `${k.replace(/_/g, " ")} ${v}`)
                .join(" · ")}
            </p>
          )}
        </form>

        <form
          className={styles.tool}
          onSubmit={(e) => {
            e.preventDefault();
            if (title.trim() && due) {
              onAdd({ title: title.trim(), due_date: due });
              setTitle("");
              setDue("");
            }
          }}
        >
          <p className={styles.toolLabel}>Add a manual deadline</p>
          <div className={styles.row}>
            <input
              className={styles.input}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. File response to FER"
              aria-label="Deadline title"
            />
            <input
              type="date"
              className={styles.input}
              value={due}
              onChange={(e) => setDue(e.target.value)}
              aria-label="Due date"
            />
            <Button size="sm" variant="secondary" type="submit">
              Add
            </Button>
          </div>
        </form>
      </div>

      {sorted.length === 0 ? (
        <p className={styles.empty}>
          No deadlines yet. Derive them from a filing or priority date, or add
          one manually.
        </p>
      ) : (
        <ul className={styles.list}>
          {sorted.map((d) => {
            const u = urgency(d.due_date, d.done);
            return (
              <li
                key={d.id}
                className={`${styles.item} ${d.done ? styles.done : ""}`}
              >
                <label className={styles.check}>
                  <input
                    type="checkbox"
                    checked={d.done}
                    onChange={(e) => onToggle(d.id, e.target.checked)}
                  />
                </label>
                <div className={styles.body}>
                  <div className={styles.head}>
                    <span className={styles.title}>{d.title}</span>
                    <span className={styles.meta}>
                      <span className="mono">{d.due_date}</span>
                      {u && <Badge tone={u.tone}>{u.text}</Badge>}
                      <Badge tone="neutral" variant="soft">
                        {d.kind}
                      </Badge>
                    </span>
                  </div>
                  {d.detail && <p className={styles.detail}>{d.detail}</p>}
                  {d.citations?.length > 0 && (
                    <div className={styles.cites}>
                      {d.citations.map((c, i) => (
                        <CitationCard
                          key={c.excerpt_ref || i}
                          citation={c}
                          index={i}
                          onView={onView ? () => onView(c) : undefined}
                        />
                      ))}
                    </div>
                  )}
                </div>
                <button
                  type="button"
                  className={styles.remove}
                  onClick={() => onDelete(d.id)}
                  aria-label="Remove deadline"
                >
                  <Icon name="close" size={13} />
                </button>
              </li>
            );
          })}
        </ul>
      )}

      <p className={styles.disclaimer}>
        Indicative schedules only. Extensions, condonation of delay, and the
        exact reckoning are matter-specific — confirm against the official rules.
      </p>
    </div>
  );
}
