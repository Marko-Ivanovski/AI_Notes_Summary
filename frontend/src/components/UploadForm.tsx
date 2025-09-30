// src/components/UploadForm.tsx

import { useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { uploadPdf, fetchChunks } from "../api/api";

export function UploadForm() {
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Doc ID and chunk count
  const [docId, setDocId] = useState<number | null>(null);
  const [chunkCount, setChunkCount] = useState<number | null>(null);

  // List of chunk previews
  const [chunkList, setChunkList] = useState<
    { chunk_id: number; page: number; preview: string }[]
  >([]);

  const onFileChange = (e: ChangeEvent<HTMLInputElement>) =>
    setFile(e.target.files?.[0] ?? null);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) {
      setStatus("Please select a PDF.");
      return;
    }

    setLoading(true);
    setStatus("Uploading…");

    try {
      const resp = await uploadPdf(file, name || undefined);
      const id = resp.data.doc_id;
      const rawChunks = resp.data.chunks;
      const count = Array.isArray(rawChunks) ? rawChunks.length : rawChunks;

      setDocId(id);
      setChunkCount(count);

      setStatus(`Upload successful — ${count} chunks created.`);

      const chunksResp = await fetchChunks(id);
      setChunkList(chunksResp.data);
    } catch (err: any) {
      setStatus(
        err.response?.data?.error ||
        err.response?.data?.message ||
        "Upload failed. Check console for details."
      );
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="p-4 border rounded space-y-4">
      <div>
        <label className="block text-sm font-medium">PDF file:</label>
        <input
          type="file"
          accept="application/pdf"
          onChange={onFileChange}
          className="mt-1"
        />
      </div>

      <div>
        <label className="block text-sm font-medium">
          Document name (optional):
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="mt-1 block w-full border px-2 py-1"
        />
      </div>

      <button
        type="submit"
        disabled={loading || !file}
        className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
      >
        {loading ? "Uploading…" : "Upload"}
      </button>

      {status && <p className="mt-2">{status}</p>}

      {docId !== null && (
        <p className="font-medium">
          Document ID: <span className="text-blue-600">{docId}</span>
        </p>
      )}

      {chunkCount !== null && (
        <p className="font-medium">
          Chunks created: <span className="text-green-600">{chunkCount}</span>
        </p>
      )}

      {chunkList.length > 0 && (
        <div className="mt-4">
          <h3 className="font-semibold">Chunks Preview</h3>
          <ul className="mt-2 max-h-40 overflow-y-auto border p-2 text-sm space-y-1">
            {chunkList.map((c) => (
              <li key={c.chunk_id}>
                <strong>Page {c.page}:</strong> {c.preview}
              </li>
            ))}
          </ul>
        </div>
      )}
    </form>
  );
}
