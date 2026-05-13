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


import * as React from "react";

interface UploadedFile {
  file: File;
  id: string;
  progress?: number;
}

interface UseFileUploadReturn {
  files: UploadedFile[];
  addFiles: (fileList: FileList) => void;
  removeFile: (id: string) => void;
  clear: () => void;
  updateProgress: (id: string, progress: number) => void;
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

function useFileUpload(): UseFileUploadReturn {
  const [files, setFiles] = React.useState<UploadedFile[]>([]);

  const addFiles = React.useCallback((fileList: FileList) => {
    const newFiles: UploadedFile[] = Array.from(fileList).map((file) => ({
      file,
      id: generateId(),
      progress: 0,
    }));
    setFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const removeFile = React.useCallback((id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  }, []);

  const clear = React.useCallback(() => {
    setFiles([]);
  }, []);

  const updateProgress = React.useCallback((id: string, progress: number) => {
    setFiles((prev) =>
      prev.map((f) => (f.id === id ? { ...f, progress } : f))
    );
  }, []);

  return {
    files,
    addFiles,
    removeFile,
    clear,
    updateProgress,
  };
}

export { useFileUpload, type UploadedFile, type UseFileUploadReturn };