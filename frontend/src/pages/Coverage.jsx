import { useEffect, useState } from "react";
import { getCorpus } from "../api/client";
import AppShell from "../components/AppShell";
import PageIntro from "../components/PageIntro";
import Badge from "../components/Badge";
import Card, { CardHeader } from "../components/Card";
import Icon from "../components/Icon";
import { SkeletonLine } from "../components/Skeleton";
import styles from "./Coverage.module.css";

export default function Coverage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [open, setOpen] = useState(null); // source name whose sections are shown

  useEffect(() => {
    const ac = new AbortController();
    getCorpus({ signal: ac.signal })
      .then(setData)
      .catch((err) => {
        if (err.name !== "AbortError") setError(err.message);
      });
    return () => ac.abort();
  }, []);

  return (
    <AppShell width="wide">
      <PageIntro eyebrow="Corpus" title="What this assistant can answer from">
        Every cited answer traces to one of the instruments below. If your
        question falls outside them, the assistant escalates rather than guessing.
      </PageIntro>

      {error && <p className={styles.error}>{error}</p>}

      {!data && !error && (
        <div className={styles.list}>
          {[0, 1, 2].map((i) => (
            <div key={i} className={styles.row}>
              <SkeletonLine w="50%" />
              <SkeletonLine w="20%" />
            </div>
          ))}
        </div>
      )}

      {data && (
        <>
          <p className={styles.summary}>
            <span className="mono">{data.chunk_count}</span> passages ·{" "}
            <span className="mono">{data.source_count}</span> instruments ·{" "}
            {Object.entries(data.jurisdictions)
              .map(([j, n]) => `${n} ${j}`)
              .join(" · ")}
          </p>

          <div className={styles.list}>
            {data.sources.map((s) => (
              <Card key={s.source} tone={s.thin ? "warn" : "default"}>
                <CardHeader
                  eyebrow={[s.document_type, s.jurisdiction, s.year]
                    .filter(Boolean)
                    .join(" · ")}
                  title={s.source}
                  aside={
                    <span className={styles.counts}>
                      {s.thin && <Badge tone="warn">thin</Badge>}
                      <Badge tone="neutral">
                        <span className="mono">{s.section_count}</span> sections
                      </Badge>
                    </span>
                  }
                />
                <div className={styles.meta}>
                  {s.organization && <span>{s.organization}</span>}
                  {s.source_url && (
                    <a
                      href={s.source_url}
                      target="_blank"
                      rel="noreferrer noopener"
                      className={styles.ext}
                    >
                      Official source <Icon name="external" size={12} />
                    </a>
                  )}
                  {s.sections.length > 0 && (
                    <button
                      type="button"
                      className={styles.toggle}
                      onClick={() =>
                        setOpen(open === s.source ? null : s.source)
                      }
                    >
                      {open === s.source ? "Hide" : "Show"} sections
                    </button>
                  )}
                </div>
                {open === s.source && (
                  <p className={styles.sections}>
                    {s.sections.map((sec) => (
                      <span key={sec} className={styles.sec}>
                        {sec}
                      </span>
                    ))}
                  </p>
                )}
              </Card>
            ))}
          </div>

          <Card tone="muted">
            <CardHeader
              eyebrow="Known gaps"
              title="What the corpus does not cover yet"
            />
            <ul className={styles.gaps}>
              {data.known_gaps.map((g) => (
                <li key={g}>{g}</li>
              ))}
            </ul>
          </Card>
        </>
      )}
    </AppShell>
  );
}
