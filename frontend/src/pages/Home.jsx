import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AppShell from "../components/AppShell";
import Button from "../components/Button";
import SegmentedControl from "../components/SegmentedControl";
import Icon from "../components/Icon";
import useSpotlight from "../hooks/useSpotlight";
import styles from "./Home.module.css";

const cx = (...c) => c.filter(Boolean).join(" ");

const JURISDICTIONS = [
  { value: "india", label: "India", icon: "india" },
  { value: "international", label: "International", icon: "globe" },
];

const SDGS = [
  {
    n: 3,
    name: "Good Health & Well-being",
    color: "#4C9F38",
    note: "Safer, faster market access for authentic Ayurveda medicine.",
    featured: false,
  },
  {
    n: 9,
    name: "Industry, Innovation & Infrastructure",
    color: "#FD6925",
    note: "Lowers the IP & regulatory barrier for Ayurveda startups and MSMEs.",
    featured: true,
  },
  {
    n: 17,
    name: "Partnerships for the Goals",
    color: "#19486A",
    note: "Links practitioners and facilitators to the AYUSH / AIIA knowledge base.",
    featured: false,
  },
];

function SdgCard({ g }) {
  const spotlight = useSpotlight();
  return (
    <li
      ref={spotlight.ref}
      onMouseMove={spotlight.onMouseMove}
      onMouseLeave={spotlight.onMouseLeave}
      className={cx(styles.sdgItem, g.featured && styles.sdgFeatured, "spotlight")}
    >
      <span
        className={styles.sdgBadge}
        style={{ background: g.color }}
        aria-hidden="true"
      >
        {g.n}
      </span>
      <span className={styles.sdgText}>
        <span className={styles.sdgName}>
          SDG {g.n} · {g.name}
        </span>
        <span className={styles.sdgNote}>{g.note}</span>
      </span>
    </li>
  );
}

export default function Home() {
  const [jurisdiction, setJurisdiction] = useState("india");
  const navigate = useNavigate();

  return (
    <AppShell>
      <div className={cx(styles.hero, "grain")}>
        <p className={styles.eyebrow}>Ayurveda · IP &amp; regulatory</p>
        <h1 className={styles.title}>
          Every answer traced to a statute, treaty, or rule.
        </h1>
        <p className={styles.lede}>
          Source-cited guidance on intellectual property and regulatory
          questions for Ayurveda practitioners, researchers, startups and
          MSMEs. When the corpus can&apos;t support an answer, the assistant
          escalates to a human rather than guess.
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

      <section className={styles.sdg}>
        <h2 className={styles.sdgTitle}>
          Aligned with the UN Sustainable Development Goals
        </h2>
        <ul className={styles.sdgList}>
          {SDGS.map((g) => (
            <SdgCard key={g.n} g={g} />
          ))}
        </ul>
      </section>

      <p className={styles.disclaimer}>
        For educational and informational purposes only — not legal advice. Do
        not enter confidential or sensitive personal data.
      </p>
    </AppShell>
  );
}
