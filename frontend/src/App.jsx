import { useCallback, useEffect, useState } from "react";
import { client } from "./api/client.js";
import FilterPanel from "./components/FilterPanel.jsx";
import ImageGrid from "./components/ImageGrid.jsx";
import SearchBar from "./components/SearchBar.jsx";
import UploadModal from "./components/UploadModal.jsx";
import "./App.css";

export default function App() {
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState({});
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchImages = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      const q = query.trim();
      if (q) params.q = q;

      for (const [key, raw] of Object.entries(filters)) {
        if (raw === undefined || raw === null || raw === "") continue;
        if (key === "color_palette") continue;
        if (key === "capture_year") {
          const y = Number(raw);
          if (!Number.isNaN(y)) params.capture_year = y;
          continue;
        }
        params[key] = raw;
      }

      const { data } = await client.get("/images/search", { params });
      if (data.error) throw new Error(data.error);
      let list = data.data || [];

      const color = filters.color_palette;
      if (color) {
        list = list.filter((img) => {
          try {
            const arr = JSON.parse(img.color_palette || "[]");
            if (!Array.isArray(arr)) return false;
            return arr.map(String).includes(String(color));
          } catch {
            return false;
          }
        });
      }

      setImages(list);
    } catch (e) {
      setError(e.message || "Failed to load images");
      setImages([]);
    } finally {
      setLoading(false);
    }
  }, [query, filters]);

  useEffect(() => {
    fetchImages();
  }, [fetchImages]);

  const handleFilter = useCallback((next) => {
    setFilters(next);
  }, []);

  const handleSearch = useCallback((q) => {
    setQuery(q);
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">Fashion Inspiration</h1>
        <div className="app-header__actions">
          <SearchBar onSearch={handleSearch} />
          <UploadModal onUploadSuccess={() => fetchImages()} />
        </div>
      </header>
      <div className="app-layout">
        <FilterPanel onFilter={handleFilter} />
        <main className="app-main">
          {error && <p className="banner-error">{error}</p>}
          <ImageGrid
            images={images}
            loading={loading}
            onAnnotationsSaved={() => fetchImages()}
          />
        </main>
      </div>
    </div>
  );
}
