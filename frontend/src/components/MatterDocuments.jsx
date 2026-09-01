import { useRef, useState } from "react";
import Badge from "./Badge";
import Icon from "./Icon";
import styles from "./MatterDocuments.module.css";

const STATUS_TONE = { ready: "accent", processing: "neutral", failed: "warn" };

/**
 * Attachments tab (S20). The user's own text documents, read for context and
 * never cited.
 * documents: matter.documents [{ id, filename, status, chunk_count, bytes, error }]
 * onUpload({ filename, text }) / onDelete(docId)
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
    if (file.size > 512 * 1024) {
      setErr("File is larger than 512 KB.");
      return;
    }
    setBusy(true);
    try {
      const text = await file.text();
      await onUpload({ filename: file.name, text });
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
        sent anywhere except to generate your answers. Plain-text files (.txt,
        .md) only for now.
      </p>

      <button
        type="button"
        className={styles.upload}
        onClick={() => inputRef.current?.click()}
        disabled={busy}
      >
        <Icon name="arrowRight" size={14} />
        {busy ? "Uploading…" : "Add a text document"}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept=".txt,.md,.markdown,text/plain"
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
                    <span className="mono">{d.chunk_count} parts</span>
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
