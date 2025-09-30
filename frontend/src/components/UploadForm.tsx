// src/components/UploadForm.tsx

import { useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { uploadPdf } from "../api/api";

export function UploadForm() {
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [docId, setDocId] = useState<number | null>(null);

  const onFileChange = (e: ChangeEvent<HTMLInputElement>) =>
    setFile(e.target.files?.[0] ?? null);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) return setStatus("Please select a PDF.");
    setStatus("Uploading…");
    try {
      const resp = await uploadPdf(file, name || undefined);
      setDocId(resp.data.doc_id);
      setStatus(`Upload successful! Doc ID: ${resp.data.doc_id}`);
    } catch (err: any) {
      setStatus(
        err.response?.data?.message ||
          "Upload failed. Check console for details."
      );
      console.error(err);
    }
  };

  return (
    <form onSubmit={onSubmit} className="p-4 border rounded">
      <label>
        PDF file:
        <input type="file" accept="application/pdf" onChange={onFileChange} />
      </label>
      <label>
        Document name (optional):
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </label>
      <button type="submit" disabled={!file}>Upload</button>
      {status && <p>{status}</p>}
      {docId && <p>🎉 Your document ID is <strong>{docId}</strong></p>}
    </form>
  );
}
