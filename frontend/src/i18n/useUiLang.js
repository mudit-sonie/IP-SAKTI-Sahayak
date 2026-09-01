import { useEffect, useState } from "react";

const KEY = "ipsakti.lang";

export function getUiLang() {
  try {
    return localStorage.getItem(KEY) || "en";
  } catch {
    return "en";
  }
}

export function setUiLang(lang) {
  try {
    localStorage.setItem(KEY, lang);
  } catch {
    /* ignore */
  }
  window.dispatchEvent(new Event("ipsakti-lang"));
}

/** Current UI language, synced across components and tabs. */
export function useUiLang() {
  const [lang, setLang] = useState(getUiLang);
  useEffect(() => {
    const handler = () => setLang(getUiLang());
    window.addEventListener("ipsakti-lang", handler);
    window.addEventListener("storage", handler);
    return () => {
      window.removeEventListener("ipsakti-lang", handler);
      window.removeEventListener("storage", handler);
    };
  }, []);
  return lang;
}
