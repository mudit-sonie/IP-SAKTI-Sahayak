import { useCallback, useRef } from "react";

/**
 * Cursor-tracking spotlight for cards. Attach the returned ref to an element
 * that also has the `.spotlight` class; on mousemove it sets --spot-x/--spot-y
 * so the CSS radial overlay follows the cursor.
 */
export default function useSpotlight() {
  const ref = useRef(null);

  const onMouseMove = useCallback((e) => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    el.style.setProperty("--spot-x", `${e.clientX - rect.left}px`);
    el.style.setProperty("--spot-y", `${e.clientY - rect.top}px`);
  }, []);

  const onMouseLeave = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    el.style.removeProperty("--spot-x");
    el.style.removeProperty("--spot-y");
  }, []);

  return { ref, onMouseMove, onMouseLeave };
}
