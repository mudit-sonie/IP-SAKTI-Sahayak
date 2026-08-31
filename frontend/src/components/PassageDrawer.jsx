import { useEffect, useState } from "react";
import { getChunk } from "../api/client";
import Icon from "./Icon";
import styles from "./PassageDrawer.module.css";

/**
 * Slide-over showing the verbatim statute text behind a citation.
 * `citation` = { source, section, excerpt_ref } | null (null = closed).
 */
export default function PassageDrawer({ citation, onClose }) {
  const [chunk, setChunk] = useState(null);
  const [state, setState] = useState("idle"); // idle | loading | error

  useEffect(() => {
    if (!citation?.excerpt_ref) {
      setChunk(null);
      return;
    }
    const ac = new AbortController();
    setState("loading");
    setChunk(null);
    getChunk(citation.excerpt_ref, { signal: ac.signal })
      .then((c) => {
        setChunk(c);
        setState("idle");
      })
      .catch((err) => {
        if (err.name !== "AbortError") setState("error");
      });
    return () => ac.abort();
  }, [citation]);

  useEffect(() => {
    if (!citation) return;
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [citation, onClose]);

  if (!citation) return null;

  const heading =
    chunk?.citation ||
    (/^\s*(section|article)/i.test(citation.section)
      ? citation.section
      : `Section ${citation.section}`);
  const url = chunk?.source_url || citation.source_url;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <aside
        className={styles.panel}
        role="dialog"
        aria-label="Statute passage"
        onClick={(e) => e.stopPropagation()}
      >
        <header className={styles.head}>
          <div>
            <p className={styles.src}>{chunk?.source || citation.source}</p>
            <h3 className={styles.heading}>{heading}</h3>
          </div>
          <button className={styles.close} onClick={onClose} aria-label="Close">
            <Icon name="close" size={16} />
          </button>
        </header>

        <div className={styles.body}>
          {state === "loading" && <p className={styles.muted}>Loading passage…</p>}
          {state === "error" && (
            <p className={styles.muted}>Couldn&apos;t load this passage.</p>
          )}
          {chunk && <p className={styles.text}>{chunk.text}</p>}
        </div>

        <footer className={styles.foot}>
          <span className={styles.verbatim}>Verbatim source text — unedited</span>
          {url && (
            <a
              className={styles.link}
              href={url}
              target="_blank"
              rel="noreferrer noopener"
            >
              Open official source <Icon name="external" size={13} />
            </a>
          )}
        </footer>
      </aside>
    </div>
  );
}
