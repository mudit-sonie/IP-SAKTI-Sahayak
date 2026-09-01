import { useRef, useState } from "react";
import Badge from "./Badge";
import Icon from "./Icon";
import styles from "./MatterDocuments.module.css";

const STATUS_TONE = { ready: "accent", processing: "neutral", failed: "warn" };

const MAX_MB = 8;

/**
 * Attachments tab (S20). The user's own documents, read for context and never
 * cited.
 * documents: matter.documents [{ id, filename, status, chunk_count, page_count, error }]
 * onUpload(file: File) / onDelete(docId)
 */
export default function MatterDocuments({ documents = [], onUpload, onDelete }) {
  const inputRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  async function pick(e) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setErr(null);
    if (file.size > MAX_MB * 1024 * 1024) {
      setErr(`File is larger than ${MAX_MB} MB.`);
      return;
    }
    setBusy(true);
    try {
      await onUpload(file);
    } catch (e2) {
      setErr(e2.message || "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={styles.wrap}>
      <p className={styles.intro}>
        Attach your own working documents — draft claims, a product dossier, label
        text, prior correspondence. The assistant reads them to understand your
        question; <strong>they are never cited</strong> — every citation still
        traces to the law.
      </p>
      <p className={styles.privacy}>
        <Icon name="alert" size={12} /> Stored locally on this machine only, not
        sent anywhere except to generate your answers. PDF, Word (.docx), and
        plain-text (.txt / .md). Scanned PDFs (no text layer) aren&apos;t
        supported.
      </p>

      <button
        type="button"
        className={styles.upload}
        onClick={() => inputRef.current?.click()}
        disabled={busy}
      >
        <Icon name="arrowRight" size={14} />
        {busy ? "Uploading…" : "Add a document"}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx,.txt,.md,.markdown"
        hidden
        onChange={pick}
      />
      {err && <p className={styles.err}>{err}</p>}

      {documents.length > 0 && (
        <ul className={styles.list}>
          {documents.map((d) => (
            <li key={d.id} className={styles.item}>
              <span className={styles.main}>
                <span className={styles.name}>{d.filename}</span>
                <span className={styles.meta}>
                  <Badge tone={STATUS_TONE[d.status] || "neutral"}>
                    {d.status}
                  </Badge>
                  {d.status === "ready" && (
                    <span className="mono">
                      {d.chunk_count} parts
                      {d.page_count ? ` · ${d.page_count}p` : ""}
                    </span>
                  )}
                  {d.status === "processing" && (
                    <span className={styles.muted}>extracting…</span>
                  )}
                  {d.error && <span className={styles.error}>{d.error}</span>}
                </span>
              </span>
              <button
                type="button"
                className={styles.remove}
                onClick={() => onDelete(d.id)}
                aria-label="Remove document"
              >
                <Icon name="close" size={13} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
