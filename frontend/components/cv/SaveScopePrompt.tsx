// frontend/components/cv/SaveScopePrompt.tsx
"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

interface SaveScopePromptProps {
  onConfirm: (saveToProfile: boolean) => void;
  onCancel: () => void;
}

export function SaveScopePrompt({ onConfirm, onCancel }: SaveScopePromptProps) {
  const t = useTranslations("saveScopePrompt");
  const [remember, setRemember] = useState(false);

  function handleChoice(saveToProfile: boolean) {
    if (remember) {
      sessionStorage.setItem("finetune_save_scope", saveToProfile ? "profile" : "cv");
    }
    onConfirm(saveToProfile);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl p-6 shadow-xl max-w-sm w-full mx-4">
        <h3 className="text-sm font-bold text-neutral-dark mb-1">
          {t("saveToProfile")}
        </h3>
        <p className="text-xs text-gray-500 mb-4">
          Im Masterprofil bleibt die Änderung dauerhaft erhalten. Nur für diesen
          Lebenslauf bleibt sie auf diesen Lebenslauf beschränkt.
        </p>
        <div className="flex flex-col gap-2 mb-4">
          <button
            type="button"
            onClick={() => handleChoice(true)}
            data-testid="save-to-profile-btn"
            className="w-full bg-teal text-white font-semibold py-2.5 rounded-lg text-sm hover:opacity-90"
          >
            {t("toProfile")}
          </button>
          <button
            type="button"
            onClick={() => handleChoice(false)}
            data-testid="save-cv-only-btn"
            className="w-full border border-teal text-teal font-semibold py-2.5 rounded-lg text-sm hover:opacity-90"
          >
            {t("justThisCV")}
          </button>
        </div>
        <label className="flex items-center gap-2 text-xs text-gray-500 cursor-pointer">
          <input
            type="checkbox"
            checked={remember}
            onChange={(e) => setRemember(e.target.checked)}
            data-testid="remember-choice-checkbox"
            className="rounded"
          />
          Meine Wahl für diese Sitzung merken
        </label>
        <button
          type="button"
          onClick={onCancel}
          className="mt-3 w-full text-xs text-gray-400 hover:text-gray-600"
        >
          Abbrechen
        </button>
      </div>
    </div>
  );
}
