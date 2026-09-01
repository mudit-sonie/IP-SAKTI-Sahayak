// UI string catalog (roadmap S15 scaffold).
// Only `en` and `hi` are populated; other languages fall back to English until
// translated. Keep keys stable and namespaced.

export const LANGS = [
  { code: "en", name: "English" },
  { code: "hi", name: "हिन्दी" },
  { code: "bn", name: "বাংলা" },
  { code: "ta", name: "தமிழ்" },
  { code: "te", name: "తెలుగు" },
  { code: "mr", name: "मराठी" },
  { code: "gu", name: "ગુજરાતી" },
  { code: "kn", name: "ಕನ್ನಡ" },
  { code: "ml", name: "മലയാളം" },
];

const CATALOG = {
  en: {
    "nav.matters": "Matters",
    "nav.coverage": "Coverage",
    "nav.fees": "Fees",
    "nav.facilitator": "Facilitator",
    "app.tagline": "Ayurveda · IPR · Regulatory",
    "app.disclaimer": "Guidance only — not legal advice.",
  },
  hi: {
    "nav.matters": "मामले",
    "nav.coverage": "कवरेज",
    "nav.fees": "शुल्क",
    "nav.facilitator": "सुविधादाता",
    "app.tagline": "आयुर्वेद · बौद्धिक संपदा · विनियामक",
    "app.disclaimer": "केवल मार्गदर्शन — यह कानूनी सलाह नहीं है।",
  },
};

export function t(lang, key) {
  return (CATALOG[lang] && CATALOG[lang][key]) || CATALOG.en[key] || key;
}
