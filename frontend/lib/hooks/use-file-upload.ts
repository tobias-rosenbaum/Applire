"use client";

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