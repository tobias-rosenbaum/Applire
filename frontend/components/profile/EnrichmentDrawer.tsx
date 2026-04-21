"use client";

// Stub — full implementation in Task 8 (Profile Enrichment Drawer)
export interface EnrichmentDrawerProps {
  open: boolean;
  scope?: string;
  onClose: () => void;
}

export function EnrichmentDrawer({ open, onClose }: EnrichmentDrawerProps) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center sm:items-center"
      onClick={onClose}
    >
      <div className="bg-white rounded-t-xl sm:rounded-xl shadow-xl p-6 w-full max-w-lg" onClick={(e) => e.stopPropagation()}>
        <p className="text-sm text-gray-500">Enrichment coming soon…</p>
        <button onClick={onClose} className="mt-4 text-sm text-teal underline">
          Close
        </button>
      </div>
    </div>
  );
}
