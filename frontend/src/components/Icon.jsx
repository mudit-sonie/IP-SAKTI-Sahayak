/* Inline icon set — replaces emoji so glyphs render consistently and inherit
 * currentColor. Stroke-based, 24x24 viewBox, 1.75 stroke. */

const PATHS = {
  india: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" />
    </>
  ),
  globe: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18" />
    </>
  ),
  arrowRight: <path d="M5 12h14M13 6l6 6-6 6" />,
  arrowLeft: <path d="M19 12H5M11 6l-6 6 6 6" />,
  external: (
    <>
      <path d="M14 4h6v6" />
      <path d="M20 4 10 14" />
      <path d="M19 14v5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5" />
    </>
  ),
  check: <path d="M4 12.5 9 17.5 20 6.5" />,
  alert: (
    <>
      <path d="M12 3 2 20h20L12 3Z" />
      <path d="M12 10v5M12 18h.01" />
    </>
  ),
  thumbUp: (
    <path d="M7 11v9H4a1 1 0 0 1-1-1v-7a1 1 0 0 1 1-1h3Zm0 0 4-8a2.5 2.5 0 0 1 2.5 2.5V8h4.5a2 2 0 0 1 2 2.3l-1.3 8A2 2 0 0 1 17.7 20H7" />
  ),
  thumbDown: (
    <path d="M17 13V4h3a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1h-3Zm0 0-4 8a2.5 2.5 0 0 1-2.5-2.5V16H6a2 2 0 0 1-2-2.3l1.3-8A2 2 0 0 1 7.3 4H17" />
  ),
  close: <path d="M6 6l12 12M18 6 6 18" />,
  sun: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </>
  ),
  moon: <path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5Z" />,
  chevron: <path d="M9 6l6 6-6 6" />,
};

export default function Icon({ name, size = 18, className, ...rest }) {
  const glyph = PATHS[name];
  if (!glyph) return null;
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...rest}
    >
      {glyph}
    </svg>
  );
}
