"use client";
import React, { useCallback } from "react";
import { useDropzone } from "react-dropzone";

type UploadDropZoneProps = {
  onFileUploaded: (file: File) => void;
};

export function UploadDropZone({ onFileUploaded }: UploadDropZoneProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFileUploaded(acceptedFiles[0]);
      }
    },
    [onFileUploaded]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

  return (
    <div
      {...getRootProps()}
      className="border-2 border-dashed rounded-md p-6 text-center cursor-pointer hover:border-blue-500"
    >
      <input {...getInputProps()} />
      {isDragActive ? (
        <p>Drop the file here ...</p>
      ) : (
        <p>Drag &amp; drop a file here, or click to select a file</p>
      )}
    </div>
  );
}
