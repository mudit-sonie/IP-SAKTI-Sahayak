import { Link, useLocation } from "react-router-dom";
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

const NAV = [
  { to: "/matters", key: "nav.matters" },
  { to: "/coverage", key: "nav.coverage" },
  { to: "/fees", key: "nav.fees" },
  { to: "/facilitator", key: "nav.facilitator" },
  { to: "/analytics", key: "nav.analytics" },
];

/**
 * Page frame: fixed-height header (wordmark + optional context chips + theme
 * toggle) and footer. `context` = { jurisdiction, formulationLabel } renders the
 * chip row. `width` = "narrow" (default) | "wide".
 */
export default function AppShell({ context, width = "narrow", children }) {
  const lang = useUiLang();
  const { pathname } = useLocation();
  return (
    <div className={styles.shell}>
      <div className={styles.ambient} aria-hidden="true" />
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>
      <header className={styles.header}>
        <div className={styles.left}>
          <Link to="/" className={styles.brand}>
            IP&#8209;SAKTI <span>Sahayak</span>
          </Link>
          {NAV.map((n) => (
            <Link
              key={n.to}
              to={n.to}
              className={cx(
                styles.navLink,
                pathname.startsWith(n.to) && styles.navLinkActive
              )}
            >
              {t(lang, n.key)}
            </Link>
          ))}
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

      <main id="main-content" className={cx(styles.main, width === "wide" && styles.wide)}>
        {children}
      </main>

      <footer className={styles.footer}>
        <span>
          IP&#8209;SAKTI Sahayak ·{" "}
          <span className="mono">v0.9.0</span> · Smart India Hackathon 2026
        </span>
        <span>Guidance only — not legal advice.</span>
      </footer>
    </div>
  );
}
