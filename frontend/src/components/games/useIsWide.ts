import { useEffect, useState } from "react";

/** True from the `md` breakpoint up — games whose stage is laid out
 * differently on phones (a vertical route/lane) rather than just shrunk. */
export function useIsWide() {
  const query = "(min-width: 768px)";
  const [wide, setWide] = useState(() => window.matchMedia(query).matches);
  useEffect(() => {
    const mql = window.matchMedia(query);
    const onChange = () => setWide(mql.matches);
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);
  return wide;
}
