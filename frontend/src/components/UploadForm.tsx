// src/components/UploadForm.tsx

import { useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { uploadPdf, fetchChunks } from "../api/api";
import { useNavigate } from "react-router-dom";
import { buildChatPath } from "../api/api";

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

  const navigate = useNavigate();

  const onContinue = async () => {
    if (!file) return;

    if (docId !== null) {
      navigate(buildChatPath(docId));
      return;
    }

    try {
      setLoading(true);
      setStatus("Uploading…");

      const resp = await uploadPdf(file, name || undefined);
      const id = resp.data.doc_id;
      const rawChunks = resp.data.chunks;
      const count = Array.isArray(rawChunks) ? rawChunks.length : rawChunks;

      setDocId(id);
      setChunkCount(count);

      setStatus(`Upload successful — ${count} chunks created.`);

      fetchChunks(id)
        .then((r) => setChunkList(r.data))
        .catch(() => {});

      navigate(buildChatPath(id));
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
    <div className="min-h-screen w-full bg-emerald-50 flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-7xl bg-white rounded-2xl shadow-lg ring-1 ring-emerald-100 p-10">
        {/* Title */}
        <div className="mb-10">
          <h1 className="text-3xl font-semibold text-emerald-700">Upload Files</h1>
          <p className="text-sm text-emerald-700/70 mt-2">
            Upload documents you want to share with your team
          </p>
        </div>

        {/* Two-column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
          {/* LEFT: Dropzone + name + upload */}
          <form onSubmit={onSubmit} className="space-y-8">
            <div className="rounded-xl border-2 border-dashed border-emerald-200 bg-emerald-50/60 p-10 text-center">
              <div className="mx-auto mb-4 h-12 w-12 rounded-full bg-white shadow-sm ring-1 ring-emerald-100 grid place-items-center">
                <span className="text-emerald-600 text-xl">⬆</span>
              </div>
              <p className="text-emerald-800 text-sm">Drag and drop files here</p>
              <p className="text-emerald-800/70 text-xs my-1">— OR —</p>

              <label className="inline-block">
                <span className="sr-only">Choose file</span>
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={onFileChange}
                  className="hidden"
                />
                <span className="inline-flex items-center rounded-lg bg-emerald-600 px-4 py-2 text-white text-sm font-medium shadow hover:bg-emerald-700 cursor-pointer">
                  Browse Files
                </span>
              </label>

              {file && (
                <div className="mt-3 text-xs text-emerald-900/80">
                  Selected: <span className="font-medium">{file.name}</span>
                </div>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-emerald-900/80 mb-2">
                Document name (optional)
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="block w-full rounded-lg border border-emerald-200 bg-white px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-emerald-300"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !file}
              className="inline-flex w-full items-center justify-center rounded-lg bg-emerald-600 px-6 py-3 text-white text-base font-semibold shadow hover:bg-emerald-700 focus:outline-none focus:ring-4 focus:ring-emerald-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Uploading…" : "Upload"}
            </button>

            {status && (
              <p
                className={`text-sm ${
                  status.startsWith("Upload successful")
                    ? "text-emerald-700"
                    : "text-rose-600"
                }`}
              >
                {status}
              </p>
            )}
            <button
              type="button"
              onClick={onContinue}
              disabled={!file || loading}
              className="mt-2 inline-flex w-full items-center justify-center rounded-lg bg-black px-6 py-3 text-white text-base font-semibold shadow hover:shadow-md focus:outline-none focus:ring-4 focus:ring-emerald-200 disabled:opacity-50 disabled:cursor-not-allowed"
              title={!file ? "Attach a PDF to continue" : "Go to AI chat"}
            >
              Continue
            </button>
            <p className="text-xs text-emerald-800/70 text-center">
              “Continue” unlocks after you attach a PDF. We’ll upload (if needed) and take you to the AI chat.
            </p>
          </form>

          {/* RIGHT: Uploaded file + chunks */}
          <div className="space-y-6">
            {/* Uploaded File card */}
            <div className="rounded-xl border border-emerald-100 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-semibold text-emerald-900">
                  Uploaded File
                </h3>
                <span
                  className={`text-xs font-medium ${
                    loading
                      ? "text-emerald-700"
                      : docId !== null
                      ? "text-emerald-700"
                      : "text-emerald-800/50"
                  }`}
                >
                  {loading ? "Uploading…" : docId !== null ? "Completed" : "—"}
                </span>
              </div>

              <div className="flex items-center gap-4">
                <div className="h-10 w-10 rounded-lg bg-emerald-100 grid place-items-center text-emerald-700">
                  📄
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-emerald-900 truncate">
                    {file ? file.name : "No file selected"}
                  </div>
                  <div className="mt-3 h-2 w-full rounded-full bg-emerald-100 overflow-hidden">
                    <div
                      className={`h-2 rounded-full bg-emerald-500 transition-all ${
                        loading
                          ? "w-3/4 animate-pulse"
                          : docId !== null
                          ? "w-full"
                          : "w-0"
                      }`}
                    />
                  </div>
                </div>
                <div className="text-xs text-emerald-800/70">
                  {docId !== null ? "100%" : loading ? "75%" : ""}
                </div>
              </div>

              {(docId !== null || chunkCount !== null) && (
                <div className="mt-5 grid grid-cols-2 gap-4 text-xs">
                  {docId !== null && (
                    <div className="rounded-md bg-emerald-50 p-2 ring-1 ring-emerald-100">
                      <span className="text-emerald-900/80">Document ID:</span>{" "}
                      <span className="font-semibold text-emerald-700">
                        {docId}
                      </span>
                    </div>
                  )}
                  {chunkCount !== null && (
                    <div className="rounded-md bg-emerald-50 p-2 ring-1 ring-emerald-100">
                      <span className="text-emerald-900/80">Chunks:</span>{" "}
                      <span className="font-semibold text-emerald-700">
                        {chunkCount}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Chunks list */}
            <div className="rounded-xl border border-emerald-100 bg-white p-6 shadow-sm">
              <h4 className="text-base font-semibold text-emerald-900 mb-3">
                Chunks Preview
              </h4>

              {chunkList.length === 0 ? (
                <p className="text-sm text-emerald-800/70">No chunks yet.</p>
              ) : (
                <ul className="space-y-3 max-h-64 overflow-y-auto pr-1">
                  {chunkList.map((c) => (
                    <li
                      key={c.chunk_id}
                      className="rounded-lg border border-emerald-100 bg-emerald-50/60 px-3 py-2 text-sm text-emerald-900"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium">Page {c.page}</span>
                        <span className="text-xs text-emerald-800/70">
                          #{c.chunk_id}
                        </span>
                      </div>
                      <p className="mt-1 line-clamp-2">{c.preview}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
