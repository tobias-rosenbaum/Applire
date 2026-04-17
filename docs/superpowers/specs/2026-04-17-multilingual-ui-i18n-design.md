# Spec: Multilingual UI (i18n) — German & English Support

**Date:** 2026-04-17  
**Status:** Draft  
**Sprint:** TBD (i18n sprint)  
**Author:** Brainstorming session with Tobias Rosenbaum

---

## Problem

Applire targets the DACH market but its UI is entirely in English, while some components (e.g. `DefaultColorPicker` in Settings) already use German strings. LLM-generated interview questions switch language unpredictably. The product needs consistent German and English support from the start.

**Scope of this sprint:**  
Full UI translation (DE + EN) using next-intl in non-routing mode.  
**Deferred to next sprint:** LLM prompt language consistency (interview questions, gap labels from LLM).

---

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| i18n library | next-intl (non-routing mode) | Best-in-class for Next.js App Router; no URL restructuring needed for auth-only app |
| Languages | DE + EN | DACH primary market; extensible to FR/ES/others later with no architecture change |
| Language detection | Browser `Accept-Language` on first visit | Auto-detects DACH users; no friction |
| Fallback locale | `en` | Safer for international visitors (Priya persona) |
| Language persistence | `user_settings.ui_language` (backend) | Syncs across devices; `user_settings` table already exists |
| Language override | Settings page, DE/EN toggle | User can always change their preference |
| JD language | Continues to drive generated document content (CV, cover letter) | Separate concern — not the user's UI language |

---

## Architecture

### Language Resolution Chain

```
Browser request
  → LocaleProvider mounts → GET /api/settings
    ├── ui_language is set → use stored value
    └── ui_language is NULL (first visit)
          → backend reads Accept-Language header
          → "de*" → store "de", return "de"
          → anything else → store "en", return "en"
  → LocaleProvider passes locale to NextIntlClientProvider
  → All useTranslations() calls resolve against messages/{locale}.json
```

### Language Change Flow

```
User clicks DE/EN in Settings
  → PATCH /api/settings { ui_language: "de" | "en" }
  → LocaleProvider re-fetches locale
  → NextIntlClientProvider updates
  → All strings re-render in new locale (no page reload)
```

### Loading State

While the locale fetch is in-flight, the app renders with `en` as the optimistic default. For returning users this is imperceptible (<50ms backend response). No flash of untranslated content.

---

## Backend Changes

### Database

New Alembic migration adds one column to `user_settings`:

```sql
ALTER TABLE user_settings ADD COLUMN ui_language VARCHAR(5) DEFAULT NULL;
-- NULL = not yet detected (first visit triggers auto-detection)
-- Allowed values: 'de', 'en'
```

Existing rows receive `NULL`, which triggers detection on next `GET /api/settings` call.

### `GET /api/settings` — Language Detection Logic

When `ui_language` is `NULL`:
1. Read `Accept-Language` request header
2. Extract primary language tag (e.g. `de-DE` → `de`, `en-US` → `en`)
3. Map: `de*` → `"de"`, anything else → `"en"`
4. Persist to `user_settings.ui_language`
5. Return detected value

On subsequent calls: return stored value directly.

### `PATCH /api/settings` — Language Update

Accept `ui_language: "de" | "en"` alongside the existing `default_accent_hex` field.  
Validate: value must be one of `["de", "en"]` — return HTTP 422 otherwise.

**No new endpoints required** — the existing settings router is extended.

### Future Language Extension

To add a new language (e.g. `es`, `fr`):
1. Add the code to the allowed values validation in `PATCH /api/settings`
2. Update the `Accept-Language` detection mapping
3. Add `messages/es.json` to the frontend
4. Add button to the language switcher component

No structural backend or frontend changes needed.

---

## Frontend Changes

### File Structure

```
frontend/
  messages/
    de.json          ← all German UI strings
    en.json          ← all English UI strings
  lib/
    providers/
      locale-provider.tsx   ← fetches locale from /api/settings, wraps NextIntlClientProvider
  app/
    layout.tsx        ← mounts LocaleProvider
    settings/
      page.tsx        ← adds LanguageSwitcher section (fully translated)
```

### LocaleProvider (`lib/providers/locale-provider.tsx`)

- Client component
- On mount: calls `GET /api/settings`, reads `ui_language`
- Provides `locale` to `NextIntlClientProvider` from next-intl
- Exposes a `setLocale(lang)` function that calls `PATCH /api/settings` and re-fetches
- Optimistic default: `"en"` while fetch is in-flight

### Language Switcher (Settings page)

New section added to `app/settings/page.tsx`, positioned above "Standard-Farbe":

```
┌─────────────────────────────────────────────────┐
│ Language / Sprache                               │
│                                                  │
│  [  DE  ]  [  EN  ]   ← toggle, active highlighted │
└─────────────────────────────────────────────────┘
```

- Calls `PATCH /api/settings { ui_language }` on click
- Triggers locale reload via `LocaleProvider.setLocale()`
- Page immediately re-renders in new language (no reload)

### Translation Key Namespaces

Translation files are namespaced by feature area:

```json
{
  "common": {
    "save": "Speichern",
    "cancel": "Abbrechen",
    "loading": "Lädt…",
    "error": "Fehler",
    "back": "Zurück",
    "delete": "Löschen",
    "export": "Exportieren",
    "download": "Herunterladen",
    "send": "Senden",
    "close": "Schließen"
  },
  "nav": {
    "dashboard": "Dashboard",
    "profile": "Mein Profil",
    "settings": "Einstellungen",
    "admin": "Admin",
    "help": "Hilfe"
  },
  "home": {
    "tagline": "KI-gestützte Bewerbungsmappe",
    "yourCVs": "Deine Lebensläufe",
    "cvUploadHint": "Lade 2–4 Lebensläufe hoch für das vollständigste Profil. Wir führen sie automatisch zusammen.",
    "jobDescription": "Stellenbeschreibung",
    "jdHint": "Füge eine Stelle ein, damit wir dein Profil sofort zuschneiden können.",
    "pasteText": "Text einfügen",
    "optional": "(Optional — du kannst das später hinzufügen)",
    "analyzeButton": "Analysieren & Profil erstellen",
    "uploadAtLeastOne": "Lade mindestens einen Lebenslauf hoch, um fortzufahren",
    "usuallyTakes": "Das dauert normalerweise ca. 30 Sekunden"
  },
  "processing": {
    "analyzingJD": "Stellenbeschreibung wird analysiert…",
    "buildingProfile": "Profil wird erstellt…",
    "jdSkipped": "Stellenbeschreibung übersprungen",
    "jdUrlInvalid": "Diese URL sieht nicht gültig aus — du kannst sie später hinzufügen",
    "jdFetchFailed": "Die Seite hat uns blockiert — du kannst den Text später einfügen"
  },
  "gaps": {
    "title": "Lückenanalyse",
    "matchScore": "Übereinstimmung",
    "strengths": "Stärken",
    "categoryB": "Wahrscheinlich vorhanden",
    "categoryC": "Nicht nachgewiesen",
    "startInterview": "Interview starten",
    "jdMissingBannerUrl": "Diese URL sah nicht gültig aus. Füge den Stellenbeschreibungstext ein, um die Lückenanalyse auszuführen.",
    "jdMissingBannerFetch": "Wir konnten die Stelle nicht laden — sie ist möglicherweise blockiert oder nicht mehr verfügbar. Füge den Text ein.",
    "addJobDescription": "Stellenbeschreibung hinzufügen →"
  },
  "interview": {
    "loading": "Interview wird gestartet…",
    "questionOf": "Frage {current} von ~{total}",
    "closingGapsFor": "Lücken werden geschlossen für",
    "gapsRemaining": "{count} Lücke(n) verbleibend",
    "categoryBBadge": "Wir vermuten, dass du diese Erfahrung hast — hilf uns, das zu bestätigen.",
    "discrepancyDetected": "Abweichung festgestellt",
    "keepOld": "Behalten: \"{value}\"",
    "useNew": "Verwenden: \"{value}\"",
    "placeholder": "Tippe deine Antwort… (Enter zum Senden, Shift+Enter für neue Zeile)",
    "done": "Ich bin fertig",
    "send": "Senden",
    "resumeBanner": "Willkommen zurück — du machst weiter, wo du aufgehört hast.",
    "gapsRemainingConfirm": "Du hast noch {count} offene Lücke(n) — bist du sicher, dass du beenden möchtest?",
    "endInterview": "Interview beenden",
    "continue": "Weiter",
    "profileCompleteness": "Profilvollständigkeit",
    "questionsAnswered": "Beantwortete Fragen",
    "gapsResolved": "Geschlossene Lücken",
    "generateCV": "Maßgeschneiderten Lebenslauf erstellen",
    "viewProfile": "Aktualisiertes Profil anzeigen",
    "reasonLabels": {
      "gaps_resolved": "Interview abgeschlossen — Lücken geschlossen!",
      "user_ended": "Interview beendet",
      "max_questions_reached": "Fragelimit erreicht"
    },
    "completionSubtitle": {
      "gaps_resolved": "Gut gemacht! Dein Profil wurde angereichert.",
      "other": "Deine Antworten wurden in deinem Master-Profil gespeichert."
    },
    "roleRequirements": "Rollenanforderungen"
  },
  "cv": {
    "generating": "Lebenslauf wird erstellt…",
    "download": "PDF herunterladen",
    "regenerate": "Neu erstellen",
    "allGapsClosed": "Alle Lücken geschlossen",
    "saveToProfile": "Im Profil speichern",
    "justThisCV": "Nur für diesen Lebenslauf",
    "unsavedChanges": "Ungespeicherte Änderungen verwerfen?",
    "discard": "Verwerfen",
    "keepEditing": "Weiter bearbeiten",
    "previewOutdated": "Vorschau könnte veraltet sein",
    "contentTab": "Inhalt",
    "actionsTab": "Aktionen",
    "designTab": "Design",
    "writeMyself": "Selbst schreiben",
    "letKaileHelp": "Kaile helfen lassen",
    "rewriteSection": "Abschnitt neu schreiben",
    "apply": "Übernehmen",
    "editFirst": "Zuerst bearbeiten",
    "discardSuggestion": "Verwerfen",
    "colorAutoDetected": "automatisch erkannt",
    "applyColor": "Farbe übernehmen",
    "defaultColor": "Standard-Farbe"
  },
  "coverLetter": {
    "generate": "Anschreiben erstellen",
    "generating": "Anschreiben wird erstellt…",
    "download": "PDF herunterladen",
    "regenerate": "Neu erstellen",
    "viewCV": "← Lebenslauf anzeigen",
    "viewCoverLetter": "Anschreiben anzeigen →"
  },
  "settings": {
    "title": "Einstellungen",
    "language": "Sprache / Language",
    "languageHint": "Wähle die Sprache der Benutzeroberfläche.",
    "dataPrivacy": "Daten & Datenschutz",
    "gdprHint": "Verwalte deine persönlichen Daten gemäß DSGVO (Art. 17 & 20).",
    "exportMyData": "Meine Daten exportieren",
    "exportHint": "Lade einen vollständigen JSON-Export aller deiner Daten herunter (DSGVO Art. 20).",
    "deleteAllData": "Alle meine Daten löschen",
    "deleteHint": "Lösche dauerhaft alle deine Daten, einschließlich Bewerbungen, Lebensläufe und Profil (DSGVO Art. 17).",
    "exporting": "Exportiere…",
    "confirmDeletion": "Datenlöschung bestätigen",
    "deletionIrreversible": "Diese Aktion ist unwiderruflich. Alle deine Daten werden dauerhaft gelöscht:",
    "deletionList": {
      "masterProfile": "Master-Profil und Anreicherungshistorie",
      "applications": "Alle Bewerbungen und deren Ablaufsitzungen",
      "interviews": "Interviewsitzungen und Transkripte",
      "cvs": "Generierte Lebensläufe und hochgeladene Dateien"
    },
    "typeDeleteToConfirm": "Gib DELETE ein zur Bestätigung:",
    "confirmDelete": "Löschen bestätigen",
    "deleting": "Wird gelöscht…",
    "defaultCVColor": "Standard-Farbe für Lebensläufe",
    "defaultCVColorHint": "Wird verwendet, wenn keine Firmenfarbe erkannt werden kann.",
    "saved": "Gespeichert ✓"
  },
  "dashboard": {
    "newApplication": "Neue Bewerbung",
    "profileCompleteness": "Profilvollständigkeit",
    "recentApplications": "Letzte Bewerbungen",
    "resumeApplication": "Weiter",
    "noApplications": "Noch keine Bewerbungen"
  },
  "profile": {
    "title": "Mein Profil"
  },
  "errors": {
    "uploadAtLeastOne": "Bitte lade mindestens einen Lebenslauf hoch, um fortzufahren.",
    "exportFailed": "Export fehlgeschlagen. Bitte versuche es erneut.",
    "deletionFailed": "Löschen fehlgeschlagen. Bitte versuche es erneut.",
    "typeDeleteToConfirm": "Bitte gib \"DELETE\" ein zur Bestätigung.",
    "flowNotFound": "Ablauf nicht gefunden",
    "failedToStart": "Interview konnte nicht gestartet werden",
    "http504": "Das dauert länger als üblich. Bitte versuche es erneut.",
    "http503": "Dienst vorübergehend ausgelastet. Bitte warte und versuche es erneut.",
    "http502": "Verarbeitungsfehler. Bitte versuche ein anderes Format."
  }
}
```

The English `messages/en.json` mirrors the same key structure with English values (largely the current hardcoded strings).

### Components to Update

Every component containing hardcoded UI strings is updated to use `useTranslations()`. Major files:

| File | Strings affected |
|---|---|
| `app/page.tsx` | Landing page labels, CTA, hints |
| `app/settings/page.tsx` | All settings labels + new language switcher |
| `app/flow/[flowId]/interview/page.tsx` | All interview UI strings |
| `app/flow/[flowId]/gaps/page.tsx` | Gap page labels, banners |
| `app/flow/[flowId]/cv/page.tsx` | CV page labels |
| `app/flow/[flowId]/cover-letter/page.tsx` | Cover letter labels |
| `app/flow/[flowId]/processing/page.tsx` | Processing overlay messages |
| `components/dashboard/Dashboard.tsx` | Dashboard labels |
| `components/dashboard/NewApplicationModal.tsx` | Modal labels |
| `components/cv/RefinementPanel.tsx` | Tab labels |
| `components/cv/ContentTab.tsx` | Section editor labels |
| `components/cv/KaileChat.tsx` | KaileChat UI |
| `components/cv/SectionEditor.tsx` | Editor labels |
| `components/cv/GapHint.tsx` | Gap hint labels |
| `components/cv/ActionsTab.tsx` | Action labels |
| `components/cv/DesignTab.tsx` | Design tab labels |
| `components/cover-letter/*.tsx` | Cover letter components |
| `components/processing-overlay.tsx` | Processing messages |

---

## User Journeys & Epics Impact

### Impacted Journeys

**All personas (Marcus, Emma, Priya, Felix, Jason, Kaile):** Every UI touchpoint now renders in the user's preferred language. No structural journey change — the flow is identical, the language is consistent.

**Priya (International Relocator):** Particularly relevant — she may prefer English UI even while targeting German jobs. Language preference is independent of CV/JD language, which is correct. The cultural adaptation content (DACH CV norms) should still be in DE or EN depending on her preference.

**Felix (Finetuner):** Section labels, gap card labels, KaileChat UI, tab labels all now respect locale. The Finetuner journey touchpoint inventory is fully covered by the components table above.

### New Epic

**E025 — Multilingual UI (i18n)**

| User Story | Title | Persona | Priority |
|---|---|---|---|
| US-i18n-01 | Auto-detect UI language from browser on first visit | All | High |
| US-i18n-02 | Store UI language preference in user_settings | All | High |
| US-i18n-03 | Language switcher in Settings (DE / EN) | All | High |
| US-i18n-04 | Full German (DE) translation of all UI strings | All | High |
| US-i18n-05 | next-intl LocaleProvider integration | All (technical) | High |

### Partially Impacted Epics

| Epic | Impact |
|---|---|
| E003 Unified Interview | UI strings fixed this sprint; LLM question language deferred to next sprint |
| E021 CV Section Editor (Finetuner) | All component strings translated |
| E010 Onboarding | Onboarding messages translated |
| E024 JD Input Resilience | Recovery banners translated |
| E023 CV Color Profiles | Settings section translated |

---

## Out of Scope (this sprint)

- LLM interview question language (deferred — separate sprint)
- LLM gap label language (deferred — same sprint as interview language)
- Cookie/localStorage pre-auth language preference (parked by user)
- Languages beyond DE and EN
- CV/cover letter document language (already handled by JD language detection)

---

## Testing

| Layer | What to test |
|---|---|
| Backend unit | `GET /api/settings` with NULL `ui_language`: correct detection from `Accept-Language` header (de-DE → de, fr-FR → en, en-US → en) |
| Backend unit | `PATCH /api/settings` with `ui_language`: valid values accepted, invalid values return 422 |
| Frontend Vitest | `LocaleProvider` renders children in correct locale; PATCH called on language switch |
| Frontend Vitest | Each translated component renders correct strings for `de` and `en` |
| E2E (Playwright) | Visit app with `Accept-Language: de` header → UI renders in German |
| E2E (Playwright) | Switch language in Settings → UI immediately re-renders in new locale |
| Manual QA | Full flow in DE: landing → upload → gaps → interview → CV → settings. No English strings visible. |
| Manual QA | Full flow in EN: same. No German strings visible (except content extracted from German CVs/JDs). |

---

## ADR Note

This sprint introduces a UI language preference stored in `user_settings` and a `LocaleProvider` pattern. If the architecture team deems this warrants a formal ADR entry (language strategy for a multilingual DACH product), it should be added to `Documents/Architecture/ADR.md` before implementation begins.
