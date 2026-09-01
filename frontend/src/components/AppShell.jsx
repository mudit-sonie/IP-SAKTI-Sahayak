import { Link } from "react-router-dom";
import styles from "./AppShell.module.css";
import Badge from "./Badge";
import Icon from "./Icon";
import ThemeToggle from "./ThemeToggle";
import { LANGS, t } from "../i18n/strings";
import { useUiLang, setUiLang } from "../i18n/useUiLang";

const cx = (...c) => c.filter(Boolean).join(" ");

const JurisdictionChip = ({ value }) => (
  <Badge tone="accent">
    <Icon name={value === "international" ? "globe" : "india"} size={13} />
    {value === "international" ? "International" : "India"}
  </Badge>
);

/**
 * Page frame: fixed-height header (wordmark + optional context chips + theme
 * toggle) and footer. `context` = { jurisdiction, formulationLabel } renders the
 * chip row. `width` = "narrow" (default) | "wide".
 */
export default function AppShell({ context, width = "narrow", children }) {
  const lang = useUiLang();
  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <div className={styles.left}>
          <Link to="/" className={styles.brand}>
            IP&#8209;SAKTI <span>Sahayak</span>
          </Link>
          <Link to="/matters" className={styles.navLink}>
            {t(lang, "nav.matters")}
          </Link>
          <Link to="/coverage" className={styles.navLink}>
            {t(lang, "nav.coverage")}
          </Link>
          <Link to="/fees" className={styles.navLink}>
            {t(lang, "nav.fees")}
          </Link>
          <Link to="/facilitator" className={styles.navLink}>
            {t(lang, "nav.facilitator")}
          </Link>
          <Link to="/analytics" className={styles.navLink}>
            {t(lang, "nav.analytics")}
          </Link>
        </div>

        <div className={styles.right}>
          {context ? (
            <div className={styles.context}>
              <JurisdictionChip value={context.jurisdiction} />
              {context.formulationLabel && (
                <Badge tone="neutral">{context.formulationLabel}</Badge>
              )}
            </div>
          ) : (
            <span className={styles.tagline}>{t(lang, "app.tagline")}</span>
          )}
          <select
            className={styles.langSelect}
            value={lang}
            onChange={(e) => setUiLang(e.target.value)}
            aria-label="Language"
          >
            {LANGS.map((l) => (
              <option key={l.code} value={l.code}>
                {l.name}
              </option>
            ))}
          </select>
          <ThemeToggle />
        </div>
      </header>

      <main className={cx(styles.main, width === "wide" && styles.wide)}>
        {children}
      </main>

      <footer className={styles.footer}>
        <span>
          IP&#8209;SAKTI Sahayak — Smart India Hackathon 2026 ·{" "}
          <span className="mono">PS&nbsp;26045</span>
        </span>
        <span>Guidance only — not legal advice.</span>
      </footer>
    </div>
  );
}
