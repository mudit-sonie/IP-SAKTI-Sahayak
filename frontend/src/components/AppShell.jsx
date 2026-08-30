import { Link } from "react-router-dom";
import styles from "./AppShell.module.css";
import Badge from "./Badge";

const cx = (...c) => c.filter(Boolean).join(" ");

const jurisdictionLabel = (j) =>
  j === "international" ? "🌍 International" : "🇮🇳 India";

/**
 * Page frame: fixed-height header (wordmark + optional context chips) and footer.
 * `context` = { jurisdiction, formulationLabel } renders the chip row.
 * `width` = "narrow" (default) | "wide".
 */
export default function AppShell({ context, width = "narrow", children }) {
  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <Link to="/" className={styles.brand}>
          IP-SAKTI <span>Sahayak</span>
        </Link>
        {context ? (
          <div className={styles.context}>
            <Badge tone="accent">{jurisdictionLabel(context.jurisdiction)}</Badge>
            {context.formulationLabel && (
              <Badge tone="neutral">{context.formulationLabel}</Badge>
            )}
          </div>
        ) : (
          <span className={styles.tagline}>Ayurveda · IPR · Regulatory</span>
        )}
      </header>

      <main className={cx(styles.main, width === "wide" && styles.wide)}>
        {children}
      </main>

      <footer className={styles.footer}>
        <span>IP-SAKTI Sahayak — Smart India Hackathon 2026 · PS 26045</span>
        <span>Guidance only — not legal advice.</span>
      </footer>
    </div>
  );
}
