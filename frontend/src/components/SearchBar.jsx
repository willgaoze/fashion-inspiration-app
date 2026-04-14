import { useEffect, useState } from "react";

export default function SearchBar({ onSearch, placeholder = "Search inspiration…" }) {
  const [value, setValue] = useState("");

  useEffect(() => {
    const t = setTimeout(() => {
      onSearch(value);
    }, 320);
    return () => clearTimeout(t);
  }, [value, onSearch]);

  return (
    <div className="search-bar">
      <input
        type="search"
        className="search-bar__input"
        value={value}
        placeholder={placeholder}
        onChange={(e) => setValue(e.target.value)}
        aria-label="Search"
      />
    </div>
  );
}
