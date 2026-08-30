import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import Button from "../components/Button";
import styles from "./Home.module.css";

const cx = (...c) => c.filter(Boolean).join(" ");

export default function Home() {
  const [jurisdiction, setJurisdiction] = useState("india");
  const navigate = useNavigate();

  return (
    <AppShell>
      <div className={styles.hero}>
        <p className={styles.eyebrow}>AI-powered IP &amp; regulatory assistant</p>
        <h1 className={styles.title}>
          Protecting Ayurveda&apos;s{" "}
          <span>innovation &amp; knowledge</span>
        </h1>
        <p className={styles.lede}>
          Source-cited guidance on intellectual property and regulatory questions
          for Ayurveda practitioners, researchers, startups and MSMEs. Every
          answer traces to a real statute or treaty section — or it escalates to
          a human.
        </p>
      </div>

      <div className={styles.card}>
        <h2 className={styles.cardTitle}>Choose your jurisdiction</h2>
        <p className={styles.cardSub}>
          The legal framework your answer will be grounded in.
        </p>

        <div className={styles.toggle} role="radiogroup" aria-label="Jurisdiction">
          {[
            ["india", "🇮🇳 India"],
            ["international", "🌍 International"],
          ].map(([value, label]) => (
            <button
              key={value}
              type="button"
              role="radio"
              aria-checked={jurisdiction === value}
              className={cx(styles.opt, jurisdiction === value && styles.optOn)}
              onClick={() => setJurisdiction(value)}
            >
              {label}
            </button>
          ))}
        </div>

        <Button
          className={styles.cta}
          onClick={() => navigate("/classify", { state: { jurisdiction } })}
        >
          Start with formulation classification →
        </Button>
      </div>

      <p className={styles.disclaimer}>
        For educational and informational purposes only. Not legal advice. Do not
        enter confidential or sensitive personal data.
      </p>
    </AppShell>
  );
}
