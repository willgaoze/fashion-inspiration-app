import { useEffect, useState } from "react";
import { client } from "../api/client";

export default function AnnotationPanel({ image, onSaved }) {
  const [notes, setNotes] = useState(image.user_notes || "");
  const [tags, setTags] = useState(image.user_tags || "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setNotes(image.user_notes || "");
    setTags(image.user_tags || "");
    setError(null);
  }, [image.id, image.user_notes, image.user_tags]);

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      const payload = {
        user_notes: notes,
        user_tags: tags || null,
      };
      const { data } = await client.patch(`/images/${image.id}/annotations`, payload);
      if (data.error) throw new Error(data.error);
      onSaved?.(data.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="annotation-panel">
      <h4 className="annotation-panel__title">Your annotations</h4>
      <label className="annotation-panel__field">
        <span>Notes</span>
        <textarea
          rows={4}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Designer notes…"
        />
      </label>
      <label className="annotation-panel__field">
        <span>Tags (JSON array string)</span>
        <input
          type="text"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          placeholder='e.g. ["market", "denim"]'
        />
      </label>
      <button type="button" className="btn btn--secondary" disabled={saving} onClick={save}>
        {saving ? "Saving…" : "Save annotations"}
      </button>
      {error && <p className="filter-panel__error">{error}</p>}
    </div>
  );
}
