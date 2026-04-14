import { useEffect, useState } from "react";
import AnnotationPanel from "./AnnotationPanel.jsx";

function SafeImage({ src, alt, className, imgClassName }) {
  const [broken, setBroken] = useState(false);
  if (broken) {
    return (
      <div className={className} role="img" aria-label={alt || "Image unavailable"}>
        <div className="image-fallback">
          <span>No preview</span>
          <small>File missing or path invalid</small>
        </div>
      </div>
    );
  }
  return (
    <div className={className}>
      <img
        src={src}
        alt={alt || ""}
        className={imgClassName}
        loading="lazy"
        onError={() => setBroken(true)}
      />
    </div>
  );
}

function DetailField({ label, value }) {
  if (value === null || value === undefined || value === "") return null;
  return (
    <div className="detail-field">
      <div className="detail-field__label">{label}</div>
      <div className="detail-field__value">{String(value)}</div>
    </div>
  );
}

export default function ImageGrid({ images, loading, onAnnotationsSaved }) {
  const [detail, setDetail] = useState(null);

  useEffect(() => {
    if (!detail) return;
    const match = images.find((i) => i.id === detail.id);
    if (match) setDetail(match);
  }, [images, detail]);

  const close = () => setDetail(null);

  return (
    <div className="image-grid-wrap">
      {loading && <p className="image-grid__muted">Loading…</p>}
      {!loading && images.length === 0 && (
        <p className="image-grid__muted">No images match your filters.</p>
      )}
      <div className="image-grid">
        {images.map((img) => (
          <button
            key={img.id}
            type="button"
            className="image-card"
            onClick={() => setDetail(img)}
          >
            <SafeImage
              src={img.filepath}
              alt={img.filename || ""}
              className="image-card__media"
              imgClassName="image-card__img"
            />
            <div className="image-card__meta">
              <div className="image-card__line">{img.garment_type || "—"}</div>
              <div className="image-card__line image-card__line--sub">
                {img.style || "—"}
              </div>
              <div className="image-card__line image-card__line--sub">
                {img.location_country || "—"}
              </div>
            </div>
          </button>
        ))}
      </div>

      {detail && (
        <div className="modal-backdrop" role="presentation" onClick={close}>
          <div
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-label="Image detail"
            onClick={(e) => e.stopPropagation()}
          >
            <button type="button" className="modal__close" onClick={close}>
              ×
            </button>
            <div className="modal__layout">
              <div className="modal__image">
                <SafeImage
                  src={detail.filepath}
                  alt={detail.filename || ""}
                  className="modal__image-inner"
                  imgClassName="modal__img"
                />
              </div>
              <div className="modal__body">
                <h3 className="modal__title">{detail.filename}</h3>
                <div className="detail-section">
                  <DetailField label="Description" value={detail.ai_description} />
                  <DetailField label="Garment type" value={detail.garment_type} />
                  <DetailField label="Style" value={detail.style} />
                  <DetailField label="Material" value={detail.material} />
                  <DetailField label="Color palette" value={detail.color_palette} />
                  <DetailField label="Pattern" value={detail.pattern} />
                  <DetailField label="Season" value={detail.season} />
                  <DetailField label="Occasion" value={detail.occasion} />
                  <DetailField
                    label="Consumer profile"
                    value={detail.consumer_profile}
                  />
                  <DetailField label="Trend notes" value={detail.trend_notes} />
                  <DetailField label="City" value={detail.location_city} />
                  <DetailField label="Country" value={detail.location_country} />
                  <DetailField label="Continent" value={detail.location_continent} />
                  <DetailField label="Capture year" value={detail.capture_year} />
                  <DetailField label="Capture month" value={detail.capture_month} />
                  <DetailField label="User notes" value={detail.user_notes} />
                  <DetailField label="User tags" value={detail.user_tags} />
                </div>
                <AnnotationPanel
                  image={detail}
                  onSaved={(next) => {
                    setDetail(next);
                    onAnnotationsSaved?.(next);
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
