"use client";

// Placeholder — full implementation in Task 8 (FineTunePanel with section list).

interface FineTunePanelProps {
  cvId: string;
  initialHtml: string | null;
  onClose: () => void;
}

export function FineTunePanel({ onClose }: FineTunePanelProps) {
  return (
    <div className="flex-1 h-[60vh] md:h-[75vh] bg-white rounded-xl shadow-soft flex items-center justify-center">
      <button type="button" onClick={onClose} className="text-sm text-teal underline">
        Fine-tune schließen
      </button>
    </div>
  );
}
