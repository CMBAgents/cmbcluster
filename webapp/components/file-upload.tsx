"use client";

import { useState } from "react";
import { useDropzone } from "react-dropzone";
import { toast } from "sonner";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { UploadCloud, File as FileIcon, X } from "lucide-react";

type FileUploadProps = {
  storageId: string;
  onUploadSuccess?: (result: any) => void;
};

export function FileUpload({ storageId, onUploadSuccess }: FileUploadProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = (acceptedFiles: File[]) => {
    setFiles(acceptedFiles);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false, // Allow only single file uploads for simplicity
  });

  const handleUpload = async () => {
    if (files.length === 0) {
      toast.error("Please select a file to upload.");
      return;
    }

    const file = files[0];
    const formData = new FormData();
    formData.append("file", file);
    formData.append("path", ""); // Or use a state for path if needed

    setIsUploading(true);
    setUploadProgress(0);

    const xhr = new XMLHttpRequest();

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percentComplete = Math.round((event.loaded / event.total) * 100);
        setUploadProgress(percentComplete);
      }
    };

    xhr.onload = () => {
      setIsUploading(false);
      if (xhr.status >= 200 && xhr.status < 300) {
        toast.success("File uploaded successfully!");
        const result = JSON.parse(xhr.responseText);
        if (onUploadSuccess) {
          onUploadSuccess(result);
        }
        setFiles([]); // Clear file selection
      } else {
        toast.error(`Upload failed: ${xhr.statusText}`);
      }
      setUploadProgress(null);
    };

    xhr.onerror = () => {
      setIsUploading(false);
      setUploadProgress(null);
      toast.error("An error occurred during the upload. Please try again.");
    };

    xhr.open("POST", `/api/storage/${storageId}/upload`, true);
    // If you have auth tokens, you would set them here, e.g.:
    // xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    xhr.send(formData);
  };

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={`p-8 border-2 border-dashed rounded-md text-center cursor-pointer
        ${isDragActive ? "border-primary bg-primary/10" : "border-gray-300"}`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center justify-center gap-2 text-muted-foreground">
          <UploadCloud className="w-10 h-10" />
          {isDragActive ? (
            <p>Drop the file here ...</p>
          ) : (
            <p>Drag 'n' drop a file here, or click to select a file</p>
          )}
        </div>
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium">Selected file:</h4>
          <div className="flex items-center justify-between p-2 border rounded-md">
            <div className="flex items-center gap-2">
              <FileIcon className="w-5 h-5 text-gray-500" />
              <span className="text-sm">{files[0].name}</span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setFiles([])}
              disabled={isUploading}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {isUploading && uploadProgress !== null && (
        <Progress value={uploadProgress} className="w-full" />
      )}

      <Button onClick={handleUpload} disabled={isUploading || files.length === 0}>
        {isUploading ? "Uploading..." : "Upload File"}
      </Button>
    </div>
  );
}
