// frontend/components/cv/SectionEditor.tsx
// Placeholder — full implementation in Task 9 (SectionEditor, GapHint, SaveScopePrompt).
"use client";

interface GapHintItem {
  id: string;
  label: string;
}

interface SectionItem {
  section_id: string;
  label: string;
  content: string;
  has_override: boolean;
  gaps: GapHintItem[];
}

interface SectionEditorProps {
  cvId: string;
  section: SectionItem;
  onSaved: (updatedHtml: string, savedContent: string) => void;
  onUnsavedChange: (hasUnsaved: boolean) => void;
}

export function SectionEditor(_props: SectionEditorProps) {
  return null;
}
