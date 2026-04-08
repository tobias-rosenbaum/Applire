"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { PhotoManager } from "@/components/profile/PhotoManager";

interface PhotoPromptStepProps {
  /** Called when the user is ready to proceed (after upload or skip). */
  onContinue: () => void;
  /** Current photo_url from the profile. */
  currentPhotoUrl?: string | null;
  /** Called when photo is uploaded or deleted so the parent can update its state. */
  onPhotoChange?: (photoUrl: string | null) => void;
}

export function PhotoPromptStep({ onContinue, currentPhotoUrl, onPhotoChange }: PhotoPromptStepProps) {
  const [showUpload, setShowUpload] = useState(false);
  const [photoAdded, setPhotoAdded] = useState(false);

  if (showUpload) {
    return (
      <div className="max-w-sm mx-auto space-y-4">
        <p className="text-sm text-gray-500 text-center">
          Step 3 of 4 — Profile photo
        </p>
        <PhotoManager
          currentPhotoUrl={currentPhotoUrl}
          onPhotoChange={(url) => {
            setPhotoAdded(!!url);
            onPhotoChange?.(url);
          }}
        />
        <Button className="w-full" onClick={onContinue}>
          {photoAdded ? "Continue →" : "Skip and continue"}
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-sm mx-auto space-y-4">
      <p className="text-sm text-gray-500 text-center">Step 3 of 4</p>
      <h2 className="text-lg font-semibold text-gray-900 text-center">
        Add a profile photo?
      </h2>
      <p className="text-sm text-gray-600 text-center">
        German employers typically expect a professional photo on your CV.
        It&apos;s optional but recommended for DACH applications.
      </p>
      <div className="grid grid-cols-2 gap-3">
        <button
          className="border-2 border-blue-600 bg-blue-50 rounded-lg p-4 text-center hover:bg-blue-100 transition-colors"
          onClick={() => setShowUpload(true)}
        >
          <div className="text-2xl mb-1">📷</div>
          <p className="text-xs font-semibold text-blue-700">Upload photo</p>
          <p className="text-xs text-blue-500 mt-0.5">Saved to your profile</p>
        </button>
        <button
          className="border border-gray-200 bg-gray-50 rounded-lg p-4 text-center hover:bg-gray-100 transition-colors"
          onClick={onContinue}
        >
          <div className="text-2xl mb-1">⏭</div>
          <p className="text-xs font-medium text-gray-700">Skip for now</p>
          <p className="text-xs text-gray-400 mt-0.5">Generate without photo</p>
        </button>
      </div>
      <p className="text-xs text-gray-400 text-center">
        You can add a photo later in Profile → Photo
      </p>
    </div>
  );
}
