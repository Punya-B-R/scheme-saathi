export default function LanguageToggle({ language = "en", onLanguageChange }) {
  return (
    <div className="flex flex-wrap gap-1 bg-gray-100 rounded-xl p-1">
      <button
        type="button"
        onClick={() => onLanguageChange?.("en")}
        className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
          language === "en"
            ? "bg-blue-600 text-white"
            : "bg-gray-100 text-gray-600 hover:bg-gray-200"
        }`}
      >
        🇬🇧 EN
      </button>
      <button
        type="button"
        onClick={() => onLanguageChange?.("hi")}
        className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
          language === "hi"
            ? "bg-blue-600 text-white"
            : "bg-gray-100 text-gray-600 hover:bg-gray-200"
        }`}
      >
        🇮🇳 हि
      </button>
      <button
        type="button"
        onClick={() => onLanguageChange?.("kn")}
        className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
          language === "kn"
            ? "bg-blue-600 text-white"
            : "bg-gray-100 text-gray-600 hover:bg-gray-200"
        }`}
      >
        ಕ
      </button>
      <button
        type="button"
        onClick={() => onLanguageChange?.("ta")}
        className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
          language === "ta"
            ? "bg-blue-600 text-white"
            : "bg-gray-100 text-gray-600 hover:bg-gray-200"
        }`}
      >
        த
      </button>
      <button
        type="button"
        onClick={() => onLanguageChange?.("bn")}
        className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
          language === "bn"
            ? "bg-blue-600 text-white"
            : "bg-gray-100 text-gray-600 hover:bg-gray-200"
        }`}
      >
        বা
      </button>
      <button
        type="button"
        onClick={() => onLanguageChange?.("mr")}
        className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
          language === "mr"
            ? "bg-blue-600 text-white"
            : "bg-gray-100 text-gray-600 hover:bg-gray-200"
        }`}
      >
        म
      </button>
      <button
        type="button"
        onClick={() => onLanguageChange?.("gu")}
        className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
          language === "gu"
            ? "bg-blue-600 text-white"
            : "bg-gray-100 text-gray-600 hover:bg-gray-200"
        }`}
      >
        ગ
      </button>
    </div>
  );
}
