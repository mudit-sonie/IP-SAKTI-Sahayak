import { useState } from "react";
import Button from "./Button";
import styles from "./FormulationProfile.module.css";

/**
 * profile: MatterProfile  ·  onSave(profile) -> Promise
 * Editable description of the product. Its text is fed as background into every
 * question asked in the matter.
 */
export default function FormulationProfile({ profile, onSave }) {
  const [form, setForm] = useState({
    dosage_form: profile.dosage_form || "",
    key_ingredients: (profile.key_ingredients || []).join(", "),
    intended_use: profile.intended_use || "",
    process_novelty: profile.process_novelty || "",
    source_notes: profile.source_notes || "",
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const set = (k) => (e) => {
    setForm({ ...form, [k]: e.target.value });
    setSaved(false);
  };

  async function save() {
    setSaving(true);
    try {
      await onSave({
        dosage_form: form.dosage_form.trim() || null,
        key_ingredients: form.key_ingredients
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        intended_use: form.intended_use.trim() || null,
        process_novelty: form.process_novelty.trim() || null,
        source_notes: form.source_notes.trim() || null,
      });
      setSaved(true);
    } finally {
      setSaving(false);
    }
  }

  const filled =
    form.dosage_form ||
    form.key_ingredients ||
    form.intended_use ||
    form.process_novelty ||
    form.source_notes;

  return (
    <div className={styles.wrap}>
      <p className={styles.hint}>
        Fed as background into every question you ask here — the legal answer
        still comes only from the corpus.
      </p>

      <label className={styles.field}>
        <span>Dosage form</span>
        <input
          value={form.dosage_form}
          onChange={set("dosage_form")}
          placeholder="tablet, churna, taila…"
        />
      </label>

      <label className={styles.field}>
        <span>Key ingredients</span>
        <input
          value={form.key_ingredients}
          onChange={set("key_ingredients")}
          placeholder="amalaki, bibhitaki, haritaki"
        />
      </label>

      <label className={styles.field}>
        <span>Intended use / claims</span>
        <textarea
          rows={2}
          value={form.intended_use}
          onChange={set("intended_use")}
          placeholder="marketed as a digestive; no disease claim"
        />
      </label>

      <label className={styles.field}>
        <span>Novelty</span>
        <textarea
          rows={2}
          value={form.process_novelty}
          onChange={set("process_novelty")}
          placeholder="classical combination, unchanged / new indication / standardised extract"
        />
      </label>

      <label className={styles.field}>
        <span>Biological source</span>
        <textarea
          rows={2}
          value={form.source_notes}
          onChange={set("source_notes")}
          placeholder="wild-harvested from a Kerala forest / own farm / imported"
        />
      </label>

      <div className={styles.actions}>
        <Button size="sm" variant="secondary" onClick={save} disabled={saving}>
          {saving ? "Saving…" : "Save profile"}
        </Button>
        {saved && <span className={styles.saved}>Saved</span>}
        {!filled && !saved && (
          <span className={styles.saved}>Empty — nothing added to questions</span>
        )}
      </div>
    </div>
  );
}
