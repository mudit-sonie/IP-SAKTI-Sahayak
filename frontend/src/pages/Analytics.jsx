import { useEffect, useState } from "react";
import { getAnalytics } from "../api/client";
import AppShell from "../components/AppShell";
import PageIntro from "../components/PageIntro";
import Card, { CardHeader } from "../components/Card";
import { SkeletonLine } from "../components/Skeleton";
import styles from "./Analytics.module.css";

const pct = (n) => `${Math.round(n * 100)}%`;

function BarList({ data }) {
  const entries = Object.entries(data || {}).sort((a, b) => b[1] - a[1]);
  const max = Math.max(1, ...entries.map(([, v]) => v));
  if (!entries.length) return <p className={styles.muted}>No data yet.</p>;
  return (
    <ul className={styles.bars}>
      {entries.map(([k, v]) => (
        <li key={k} className={styles.bar}>
          <span className={styles.barLabel}>{k}</span>
          <span className={styles.barTrack}>
            <span
              className={styles.barFill}
              style={{ width: `${(v / max) * 100}%` }}
            />
          </span>
          <span className={styles.barVal}>{v}</span>
        </li>
      ))}
    </ul>
  );
}

export default function Analytics() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const ac = new AbortController();
    getAnalytics({ signal: ac.signal })
      .then(setData)
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => ac.abort();
  }, []);

  return (
    <AppShell width="wide">
      <PageIntro eyebrow="Usage" title="Analytics">
        Aggregate counters only — no question text and no user identifier is
        stored. Useful for spotting which topics and instruments citizens ask
        about most.
      </PageIntro>

      {error && <p className={styles.error}>{error}</p>}
      {!data && !error && <SkeletonLine w="50%" />}

      {data && (
        <>
          <div className={styles.tiles}>
            <div className={styles.tile}>
              <span className={styles.tileNum}>{data.total_queries}</span>
              <span className={styles.tileLabel}>questions</span>
            </div>
            <div className={styles.tile}>
              <span className={styles.tileNum}>{pct(data.escalation_rate)}</span>
              <span className={styles.tileLabel}>escalated</span>
            </div>
            <div className={styles.tile}>
              <span className={styles.tileNum}>{pct(data.abs_flag_rate)}</span>
              <span className={styles.tileLabel}>ABS-flagged</span>
            </div>
            <div className={styles.tile}>
              <span className={styles.tileNum}>{pct(data.from_faq_rate)}</span>
              <span className={styles.tileLabel}>from reviewed FAQ</span>
            </div>
          </div>

          <div className={styles.grid}>
            <Card>
              <CardHeader eyebrow="Breakdown" title="By status" />
              <BarList data={data.by_status} />
            </Card>
            <Card>
              <CardHeader eyebrow="Breakdown" title="By jurisdiction" />
              <BarList data={data.by_jurisdiction} />
            </Card>
            <Card>
              <CardHeader eyebrow="Breakdown" title="By formulation category" />
              <BarList data={data.by_category} />
            </Card>
            <Card>
              <CardHeader eyebrow="Topics" title="Most-cited instruments" />
              <BarList data={data.top_sources} />
            </Card>
            <Card>
              <CardHeader eyebrow="Trend" title="Questions per day" />
              <BarList data={data.by_day} />
            </Card>
          </div>
        </>
      )}
    </AppShell>
  );
}
