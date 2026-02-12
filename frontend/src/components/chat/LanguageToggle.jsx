export default function LanguageToggle({ language = "en", onLanguageChange }) {
  return (
    <div className="flex gap-1 bg-gray-100 rounded-full p-1">
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
    </div>
  );
}
