// src/api/api.ts

import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_URL || "http://localhost:5000",
  headers: { "Content-Type": "application/json" },
});

export function uploadPdf(file: File, docName?: string) {
  const form = new FormData();
  form.append("file", file);
  if (docName) form.append("doc_name", docName);
  return api.post<{ doc_id: number; chunks: any[]; message: string }>(
    "/upload",
    form,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
}
