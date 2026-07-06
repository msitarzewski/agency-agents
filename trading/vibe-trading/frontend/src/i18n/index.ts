import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import en from "./locales/en.json";
import zhCN from "./locales/zh-CN.json";

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      "zh-CN": { translation: zhCN },
    },
    // Default to English for everyone on first visit; only an explicit toggle
    // (persisted to localStorage) switches to Chinese. We intentionally do NOT
    // read `navigator` so a zh browser is not auto-switched away from English.
    fallbackLng: "en",
    interpolation: { escapeValue: false },
    detection: {
      order: ["localStorage"],
      caches: ["localStorage"],
    },
  });

export default i18n;
