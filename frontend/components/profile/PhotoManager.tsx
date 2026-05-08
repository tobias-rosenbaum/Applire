"use client";

// Copyright (C) 2024-2026 Tobias Rosenbaum
//
// This file is part of Applire.
//
// Applire is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published
// by the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Applire is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with Applire. If not, see <https://www.gnu.org/licenses/>.


import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

interface PhotoManagerProps {
  /** Called after a successful upload or delete so the parent can refresh. */
  onPhotoChange?: (photoUrl: string | null) => void;
  /** Current photo_url from the profile (file path, not data URI). */
  currentPhotoUrl?: string | null;
}

export function PhotoManager({ onPhotoChange, currentPhotoUrl }: PhotoManagerProps) {
  // Consent defaults to true when the user already has a photo (Replace path — no re-consent needed)
  const [consent, setConsent] = useState(!!currentPhotoUrl);
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [previewSrc, setPreviewSrc] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadedAt, setUploadedAt] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const hasPhoto = !!(currentPhotoUrl || previewSrc);

  // Load preview via GET /api/profile/photo when a photo exists on the server.
  // Revoke the previous object URL to avoid memory leaks.
  useEffect(() => {
    if (!currentPhotoUrl) return;
    let objectUrl: string | null = null;
    fetch(`${API_BASE}/api/profile/photo`)
      .then((r) => (r.ok ? r.blob() : null))
      .then((blob) => {
        if (blob) {
          objectUrl = URL.createObjectURL(blob);
          setPreviewSrc(objectUrl);
        }
      })
      .catch(() => { /* non-fatal */ });
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [currentPhotoUrl]);

  async function handleUpload(file: File) {
    setError(null);
    if (!consent) {
      setError("Please tick the consent checkbox before uploading.");
      return;
    }
    setUploading(true);
    try {
      const body = new FormData();
      body.append("file", file);
      const res = await fetch(`${API_BASE}/api/profile/photo?consent=true`, {
        method: "POST",
        body,
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error((err as { detail?: string }).detail ?? "Upload failed");
      }
      const data = (await res.json()) as { photo_url: string; consent_at: string };
      setUploadedAt(
        new Date(data.consent_at).toLocaleDateString("en-GB", {
          day: "numeric",
          month: "short",
          year: "numeric",
        }),
      );
      // Revoke any previous preview and show new one immediately
      setPreviewSrc((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return URL.createObjectURL(file);
      });
      onPhotoChange?.(data.photo_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete() {
    setError(null);
    setDeleting(true);
    try {
      const res = await fetch(`${API_BASE}/api/profile/photo`, { method: "DELETE" });
      if (!res.ok) throw new Error("Delete failed");
      setPreviewSrc((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
      setUploadedAt(null);
      setConsent(false);
      onPhotoChange?.(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-gray-900">Profile Photo</h3>
        <p className="text-xs text-gray-500 mt-0.5">
          Optional. Used in your CV when applying to DACH roles.
        </p>
      </div>

      {error && (
        <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
          {error}
        </p>
      )}

      {hasPhoto ? (
        /* Filled state */
        <div className="flex gap-4 items-start p-3 bg-gray-50 rounded-lg border border-gray-200">
          {previewSrc && (
            <img
              src={previewSrc}
              alt="Profile photo"
              className="w-14 h-[68px] object-cover object-top rounded"
            />
          )}
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-gray-900 truncate">Profile photo</p>
            {uploadedAt && (
              <p className="text-xs text-gray-500 mt-0.5">Uploaded {uploadedAt}</p>
            )}
            <div className="flex gap-2 mt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => inputRef.current?.click()}
                disabled={uploading}
              >
                {uploading ? "Uploading…" : "Replace"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="border-red-200 text-red-600 hover:bg-red-50"
                onClick={handleDelete}
                disabled={deleting}
              >
                {deleting ? "Deleting…" : "Delete"}
              </Button>
            </div>
          </div>
        </div>
      ) : (
        /* Empty state */
        <>
          <div
            className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50/30 transition-colors"
            onClick={() => inputRef.current?.click()}
          >
            <div className="text-2xl mb-2">📷</div>
            <p className="text-sm font-medium text-gray-700">Upload a photo</p>
            <p className="text-xs text-gray-400 mt-1">JPEG, PNG or WebP · max 5 MB</p>
          </div>

          <div className="flex gap-2 items-start bg-blue-50 border border-blue-200 rounded-lg px-3 py-2">
            <input
              type="checkbox"
              id="photo-consent"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
              className="mt-0.5 flex-shrink-0"
            />
            <label
              htmlFor="photo-consent"
              className="text-xs text-blue-800 leading-relaxed cursor-pointer"
            >
              I consent to Applire storing my profile photo to include it in generated CVs. I can
              delete it at any time.{" "}
              <a href="/privacy" className="underline">
                Privacy policy ↗
              </a>
            </label>
          </div>

          <Button
            className="w-full"
            disabled={!consent || uploading}
            onClick={() => inputRef.current?.click()}
          >
            {uploading ? "Uploading…" : "Upload photo"}
          </Button>
        </>
      )}

      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) void handleUpload(file);
          e.target.value = "";
        }}
      />

      {hasPhoto && (
        <p className="text-xs text-green-700 bg-green-50 border border-green-200 rounded px-3 py-2">
          ✓ Photo will appear in your Lebenslauf and Swiss CV templates for DACH applications.
        </p>
      )}
    </div>
  );
}
