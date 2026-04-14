import { useCallback, useEffect, useMemo, useState } from "react";
import { client } from "../api/client";

const FILTER_KEYS = [
  "garment_type",
  "style",
  "material",
  "color_palette",
  "pattern",
  "season",
  "occasion",
  "consumer_profile",
  "location_country",
  "location_continent",
  "capture_year",
];

function labelForKey(key) {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function FilterPanel({ onFilter }) {
  const [options, setOptions] = useState({});
  const [selection, setSelection] = useState(() =>
    Object.fromEntries(FILTER_KEYS.map((k) => [k, ""])),
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const emit = useCallback(
    (next) => {
      onFilter(next);
    },
    [onFilter],
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const { data } = await client.get("/filters");
        if (cancelled) return;
        if (data.error) throw new Error(data.error);
        setOptions(data.data || {});
        setError(null);
      } catch (e) {
        if (!cancelled) setError(e.message || "Failed to load filters");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const keysToRender = useMemo(() => {
    const fromApi = Object.keys(options);
    const ordered = FILTER_KEYS.filter((k) => fromApi.includes(k));
    const extra = fromApi.filter((k) => !FILTER_KEYS.includes(k));
    return [...ordered, ...extra.sort()];
  }, [options]);

  const handleChange = (key, value) => {
    setSelection((prev) => {
      const next = { ...prev, [key]: value };
      emit(next);
      return next;
    });
  };

  return (
    <aside className="filter-panel">
      <h2 className="filter-panel__title">Filters</h2>
      {loading && <p className="filter-panel__muted">Loading options…</p>}
      {error && <p className="filter-panel__error">{error}</p>}
      {!loading &&
        keysToRender.map((key) => {
          const opts = options[key];
          if (!Array.isArray(opts) || opts.length === 0) return null;
          return (
            <label key={key} className="filter-panel__field">
              <span className="filter-panel__label">{labelForKey(key)}</span>
              <select
                className="filter-panel__select"
                value={selection[key] ?? ""}
                onChange={(e) => handleChange(key, e.target.value)}
              >
                <option value="">All</option>
                {opts.map((opt) => (
                  <option key={String(opt)} value={String(opt)}>
                    {String(opt)}
                  </option>
                ))}
              </select>
            </label>
          );
        })}
    </aside>
  );
}
