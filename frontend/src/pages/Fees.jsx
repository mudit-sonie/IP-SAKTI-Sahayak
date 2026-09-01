import { useEffect, useMemo, useState } from "react";
import { getFees } from "../api/client";
import AppShell from "../components/AppShell";
import PageIntro from "../components/PageIntro";
import Card, { CardHeader } from "../components/Card";
import SegmentedControl from "../components/SegmentedControl";
import { SkeletonLine } from "../components/Skeleton";
import styles from "./Fees.module.css";

const rupees = (n) => "₹" + n.toLocaleString("en-IN");

function renewalTotal(bands, entity, from, to) {
  if (!from || !to || to < from) return 0;
  let sum = 0;
  for (const b of bands) {
    const per = b.amounts[entity];
    if (per == null) continue;
    const overlap = Math.max(
      0,
      Math.min(to, b.to_year) - Math.max(from, b.from_year) + 1,
    );
    sum += overlap * per;
  }
  return sum;
}

export default function Fees() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [track, setTrack] = useState("patent");
  const [entity, setEntity] = useState("");
  const [picked, setPicked] = useState({});
  const [rFrom, setRFrom] = useState(3);
  const [rTo, setRTo] = useState(20);

  useEffect(() => {
    const ac = new AbortController();
    getFees({ signal: ac.signal })
      .then(setData)
      .catch((err) => {
        if (err.name !== "AbortError") setError(err.message);
      });
    return () => ac.abort();
  }, []);

  const schedule = useMemo(
    () => data?.schedules.find((s) => s.track === track),
    [data, track],
  );

  useEffect(() => {
    if (schedule) {
      setEntity(schedule.entities[0].key);
      setPicked({});
    }
  }, [schedule]);

  const itemsTotal = useMemo(() => {
    if (!schedule) return 0;
    return schedule.items
      .filter((it) => picked[it.code])
      .reduce((sum, it) => sum + (it.amounts[entity] || 0), 0);
  }, [schedule, picked, entity]);

  const renewals = useMemo(
    () =>
      schedule?.renewal_bands?.length && picked.__renewal
        ? renewalTotal(schedule.renewal_bands, entity, Number(rFrom), Number(rTo))
        : 0,
    [schedule, picked, entity, rFrom, rTo],
  );

  const total = itemsTotal + renewals;

  return (
    <AppShell width="wide">
      <PageIntro eyebrow="Tools" title="Fee calculator">
        Statutory patent and GI fees at e-filing rates. Attorney charges are not
        included; government fees change by amendment — always confirm against
        the current schedule.
      </PageIntro>

      {error && <p className={styles.error}>{error}</p>}
      {!data && !error && (
        <div className={styles.loading}>
          <SkeletonLine w="40%" />
          <SkeletonLine w="70%" />
        </div>
      )}

      {schedule && (
        <div className={styles.grid}>
          <div className={styles.controls}>
            <SegmentedControl
              options={data.schedules.map((s) => ({
                value: s.track,
                label: s.track === "patent" ? "Patent" : "GI",
              }))}
              value={track}
              onChange={setTrack}
              ariaLabel="Fee track"
            />

            {schedule.entities.length > 1 && (
              <label className={styles.field}>
                <span>Applicant category</span>
                <select
                  value={entity}
                  onChange={(e) => setEntity(e.target.value)}
                >
                  {schedule.entities.map((e) => (
                    <option key={e.key} value={e.key}>
                      {e.label}
                    </option>
                  ))}
                </select>
              </label>
            )}

            <fieldset className={styles.items}>
              <legend>Items</legend>
              {schedule.items.map((it) => (
                <label key={it.code} className={styles.item}>
                  <input
                    type="checkbox"
                    checked={Boolean(picked[it.code])}
                    onChange={(e) =>
                      setPicked((p) => ({ ...p, [it.code]: e.target.checked }))
                    }
                  />
                  <span className={styles.itemLabel}>
                    {it.label}
                    {it.note && <em className={styles.note}>{it.note}</em>}
                  </span>
                  <span className={styles.itemAmt}>
                    {rupees(it.amounts[entity] || 0)}
                  </span>
                </label>
              ))}

              {schedule.renewal_bands?.length > 0 && (
                <div className={styles.renewal}>
                  <label className={styles.item}>
                    <input
                      type="checkbox"
                      checked={Boolean(picked.__renewal)}
                      onChange={(e) =>
                        setPicked((p) => ({
                          ...p,
                          __renewal: e.target.checked,
                        }))
                      }
                    />
                    <span className={styles.itemLabel}>Renewal fees</span>
                    <span className={styles.itemAmt}>{rupees(renewals)}</span>
                  </label>
                  {picked.__renewal && (
                    <div className={styles.years}>
                      <label>
                        from year
                        <input
                          type="number"
                          min="1"
                          max="20"
                          value={rFrom}
                          onChange={(e) => setRFrom(e.target.value)}
                        />
                      </label>
                      <label>
                        to year
                        <input
                          type="number"
                          min="1"
                          max="20"
                          value={rTo}
                          onChange={(e) => setRTo(e.target.value)}
                        />
                      </label>
                    </div>
                  )}
                </div>
              )}
            </fieldset>
          </div>

          <aside className={styles.summary}>
            <Card>
              <CardHeader eyebrow={schedule.title} title={rupees(total)} />
              <p className={styles.meta}>
                {schedule.source}
                {schedule.source_url && (
                  <>
                    {" · "}
                    <a
                      href={schedule.source_url}
                      target="_blank"
                      rel="noreferrer noopener"
                    >
                      official fees
                    </a>
                  </>
                )}
                <br />
                as of {schedule.as_of}
              </p>
              <ul className={styles.notes}>
                {schedule.notes.map((n) => (
                  <li key={n}>{n}</li>
                ))}
              </ul>
              <p className={styles.disclaimer}>{data.disclaimer}</p>
            </Card>
          </aside>
        </div>
      )}
    </AppShell>
  );
}
