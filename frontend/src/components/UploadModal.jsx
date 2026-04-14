import { useRef, useState } from "react";
import { client } from "../api/client";

export default function UploadModal({ onUploadSuccess }) {
  const inputRef = useRef(null);
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(null);

  const pickFile = () => {
    setMessage(null);
    inputRef.current?.click();
  };

  const onFile = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setBusy(true);
    setMessage(null);
    try {
      const body = new FormData();
      body.append("file", file);
      body.append("uploaded_by", "web-ui");
      const { data } = await client.post("/upload", body);
      if (data.error) throw new Error(data.error);
      setOpen(false);
      onUploadSuccess?.(data.data);
    } catch (err) {
      const d = err.response?.data?.detail;
      const msg = Array.isArray(d)
        ? d.map((x) => x.msg || JSON.stringify(x)).join("; ")
        : d || err.message || "Upload failed";
      setMessage(msg);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <button type="button" className="btn btn--primary" onClick={() => setOpen(true)}>
        Upload
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"
        className="visually-hidden"
        onChange={onFile}
      />
      {open && (
        <div className="modal-backdrop" role="presentation" onClick={() => !busy && setOpen(false)}>
          <div className="modal modal--sm" onClick={(e) => e.stopPropagation()}>
            <button
              type="button"
              className="modal__close"
              disabled={busy}
              onClick={() => setOpen(false)}
            >
              ×
            </button>
            <h3 className="modal__title">Upload image</h3>
            <p className="modal__hint">JPEG, PNG, or WebP up to your API limits.</p>
            <button
              type="button"
              className="btn btn--primary btn--block"
              disabled={busy}
              onClick={pickFile}
            >
              {busy ? "Uploading…" : "Choose file"}
            </button>
            {message && <p className="filter-panel__error">{message}</p>}
          </div>
        </div>
      )}
    </>
  );
}
