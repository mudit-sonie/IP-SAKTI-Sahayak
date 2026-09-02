import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { matters as mattersApi } from "../api/client";
import AppShell from "../components/AppShell";
import PageIntro from "../components/PageIntro";
import Button from "../components/Button";
import Badge from "../components/Badge";
import SegmentedControl from "../components/SegmentedControl";
import Icon from "../components/Icon";
import { SkeletonLine } from "../components/Skeleton";
import useSpotlight from "../hooks/useSpotlight";
import styles from "./Matters.module.css";

const JURISDICTIONS = [
  { value: "india", label: "India", icon: "india" },
  { value: "international", label: "International", icon: "globe" },
];

const ABS_TONE = { flagged: "warn", clear: "accent", unknown: "neutral" };

const cx = (...c) => c.filter(Boolean).join(" ");

function MatterCard({ m }) {
  const spotlight = useSpotlight();
  return (
    <li>
      <Link
        to={`/matters/${m.id}`}
        ref={spotlight.ref}
        onMouseMove={spotlight.onMouseMove}
        onMouseLeave={spotlight.onMouseLeave}
        className={cx(styles.card, "spotlight", "lift")}
      >
        <div className={styles.cardTop}>
          <h3 className={styles.cardTitle}>{m.title}</h3>
          <Badge tone={ABS_TONE[m.abs_status]} variant="soft">
            ABS: {m.abs_status}
          </Badge>
        </div>
        <p className={styles.cardMeta}>
          <Icon
            name={m.jurisdiction === "international" ? "globe" : "india"}
            size={13}
          />
          {m.formulation_label || "Not classified"}
          <span className={styles.dot}>·</span>
          <span className="mono">{m.question_count}</span> question
          {m.question_count === 1 ? "" : "s"}
        </p>
      </Link>
    </li>
  );
}

export default function Matters() {
  const navigate = useNavigate();
  const [list, setList] = useState(null);
  const [error, setError] = useState(null);
  const [title, setTitle] = useState("");
  const [jurisdiction, setJurisdiction] = useState("india");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    const ac = new AbortController();
    mattersApi
      .list({ signal: ac.signal })
      .then(setList)
      .catch((err) => {
        if (err.name !== "AbortError") setError(err.message);
      });
    return () => ac.abort();
  }, []);

  async function create(e) {
    e.preventDefault();
    const clean = title.trim();
    if (!clean || creating) return;
    setCreating(true);
    try {
      const m = await mattersApi.create({ title: clean, jurisdiction });
      navigate(`/matters/${m.id}`);
    } catch (err) {
      setError(err.message);
      setCreating(false);
    }
  }

  return (
    <AppShell>
      <PageIntro eyebrow="Workspace" title="Your matters">
        A matter is one formulation on its way to market — its classification,
        the questions you&apos;ve asked, its ABS status, and (soon) its compliance
        checklist and document drafts, all in one place.
      </PageIntro>

      <form className={styles.create} onSubmit={create}>
        <input
          className={styles.titleInput}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Name a formulation — e.g. Ashwagandha sleep churna"
          aria-label="Matter title"
        />
        <SegmentedControl
          options={JURISDICTIONS}
          value={jurisdiction}
          onChange={setJurisdiction}
          ariaLabel="Jurisdiction"
        />
        <Button type="submit" disabled={!title.trim() || creating}>
          {creating ? "Creating…" : "Create matter"}
          {!creating && <Icon name="arrowRight" size={16} />}
        </Button>
      </form>

      {error && <p className={styles.error}>{error}</p>}

      {list === null && !error && (
        <div className={styles.grid}>
          {[0, 1].map((i) => (
            <div key={i} className={styles.card}>
              <SkeletonLine w="60%" />
              <SkeletonLine w="35%" />
            </div>
          ))}
        </div>
      )}

      {list && list.length === 0 && (
        <p className={styles.empty}>
          No matters yet. Name one above, or start from the{" "}
          <Link to="/">classification flow</Link>.
        </p>
      )}

      {list && list.length > 0 && (
        <ul className={styles.grid}>
          {list.map((m) => (
            <MatterCard key={m.id} m={m} />
          ))}
        </ul>
      )}
    </AppShell>
  );
}
