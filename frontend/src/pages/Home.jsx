import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import Button from "../components/Button";
import SegmentedControl from "../components/SegmentedControl";
import Icon from "../components/Icon";
import styles from "./Home.module.css";

const JURISDICTIONS = [
  { value: "india", label: "India", icon: "india" },
  { value: "international", label: "International", icon: "globe" },
];

export default function Home() {
  const [jurisdiction, setJurisdiction] = useState("india");
  const navigate = useNavigate();

  return (
    <AppShell>
      <div className={styles.hero}>
        <p className={styles.eyebrow}>Ayurveda · IP &amp; regulatory</p>
        <h1 className={styles.title}>
          Every answer traced to a statute, treaty, or rule.
        </h1>
        <p className={styles.lede}>
          Source-cited guidance on intellectual property and regulatory questions
          for Ayurveda practitioners, researchers, startups and MSMEs. When the
          corpus can&apos;t support an answer, the assistant escalates to a human
          rather than guess.
        </p>
      </div>

      <div className={styles.panel}>
        <div className={styles.panelHead}>
          <h2 className={styles.panelTitle}>Choose your jurisdiction</h2>
          <p className={styles.panelSub}>
            The legal framework your answer will be grounded in.
          </p>
        </div>

        <SegmentedControl
          options={JURISDICTIONS}
          value={jurisdiction}
          onChange={setJurisdiction}
          ariaLabel="Jurisdiction"
        />

        <Button
          className={styles.cta}
          onClick={() => navigate("/classify", { state: { jurisdiction } })}
        >
          Start with formulation classification
          <Icon name="arrowRight" size={16} />
        </Button>
      </div>

      <p className={styles.disclaimer}>
        For educational and informational purposes only — not legal advice. Do
        not enter confidential or sensitive personal data.
      </p>
    </AppShell>
  );
}
