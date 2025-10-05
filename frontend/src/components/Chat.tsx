// src/components/Chat.tsx
import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { askQuestion, fetchChunks, buildChatPath, getPdfUrl } from "../api/api";
import * as React from "react";

type Message = {
  role: "user" | "assistant";
  content: string;
  citations?: Array<{ chunk_id: number; page?: number; preview?: string }>;
};

export function Chat() {
  const [params] = useSearchParams();
  const docIdParam = params.get("doc_id");
  const docId = useMemo(() => {
    if (!docIdParam) return null;
    const n = Number(docIdParam);
    return Number.isNaN(n) ? docIdParam : n;
  }, [docIdParam]);

  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hi! Ask me anything about your PDF. I’ll answer using only the uploaded content and include citations.",
    },
  ]);

  const [chunks, setChunks] = useState<Array<{ chunk_id: number; page: number; preview: string }>>([]);
  const [pdfSupported, setPdfSupported] = useState(true);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (!docId) return;
    fetchChunks(Number(docId))
      .then((r) => setChunks(r.data))
      .catch(() => setChunks([]));
  }, [docId]);

  // Uses getPdfUrl which should point to `/upload/<doc_id>`
  const pdfUrl = useMemo(() => (docId ? getPdfUrl(docId) : ""), [docId]);

  async function onSend() {
    if (!question.trim() || !docId) return;
    const q = question.trim();
    setQuestion("");
    setMessages((m) => [...m, { role: "user", content: q }]);
    setLoading(true);

    try {
      const { data } = await askQuestion({ doc_id: docId, question: q });
      const answer = data?.answer ?? "No answer returned.";
      const citations = Array.isArray(data?.citations)
        ? data.citations.map((cid: any) =>
            typeof cid === "number" ? { chunk_id: cid } : cid
          )
        : undefined;

      setMessages((m) => [...m, { role: "assistant", content: answer, citations }]);
    } catch (err: any) {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content:
            err?.response?.data?.error ||
            err?.response?.data?.message ||
            "Sorry—something went wrong while answering.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  }

  return (
    <div className="w-full">
      {/* Header inside the card */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-emerald-700">AI Notes Chat</h1>
          <p className="text-sm text-emerald-700/70">
            Ask questions grounded in your uploaded PDF.
          </p>
        </div>
        {docId && (
          <Link
            to={buildChatPath(Number(docId))}
            className="text-xs text-emerald-700/70 underline underline-offset-2 hover:text-emerald-800"
          >
            doc_id: {String(docId)}
          </Link>
        )}
      </div>

      {/* Two-column layout: LEFT = PDF, RIGHT = Chat */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* LEFT: PDF preview (iframe) with chunk fallback */}
        <div className="rounded-xl border border-emerald-100 bg-white shadow-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-emerald-100 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-emerald-900">Document Preview</h3>
            {pdfUrl && (
              <a
                href={pdfUrl}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-emerald-700/80 hover:text-emerald-900"
              >
                Open original
              </a>
            )}
          </div>

          {pdfUrl && pdfSupported ? (
            <iframe
              title="PDF Preview"
              src={pdfUrl}
              className="w-full h-[60vh] lg:h-[75vh]"
              onError={() => setPdfSupported(false)}
            />
          ) : (
            <div className="p-4">
              <p className="text-sm text-emerald-800/80 mb-3">
                {pdfUrl
                  ? "Preview unavailable in this browser. Showing chunk previews instead:"
                  : "No PDF URL found. Showing chunk previews:"}
              </p>
              {chunks.length === 0 ? (
                <p className="text-sm text-emerald-800/70">No chunks available.</p>
              ) : (
                <ul className="space-y-3 max-h-[70vh] overflow-y-auto pr-1">
                  {chunks.map((c) => (
                    <li
                      key={c.chunk_id}
                      className="rounded-lg border border-emerald-100 bg-emerald-50/60 px-3 py-2 text-sm text-emerald-900"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium">Page {c.page}</span>
                        <span className="text-xs text-emerald-800/70">#{c.chunk_id}</span>
                      </div>
                      <p className="mt-1 line-clamp-2">{c.preview}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>

        {/* RIGHT: Chat */}
        <div className="rounded-xl border border-emerald-100 bg-white shadow-sm flex flex-col">
          {/* Messages */}
          <div className="p-4 space-y-4 overflow-y-auto grow max-h-[70vh]">
            {messages.map((m, i) => (
              <MessageBubble key={i} role={m.role} content={m.content} citations={m.citations} />
            ))}
            <div ref={chatEndRef} />
          </div>

          {/* Composer */}
          <div className="border-t border-emerald-100 p-4">
            <div className="flex items-end gap-2">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Ask a question about your document..."
                rows={2}
                className="flex-1 rounded-lg border border-emerald-200 bg-white px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-emerald-300"
              />
              <button
                type="button"
                onClick={onSend}
                disabled={loading || !question.trim() || !docId}
                className="shrink-0 inline-flex items-center justify-center rounded-lg bg-emerald-600 px-5 py-3 text-white text-base font-semibold shadow hover:bg-emerald-700 focus:outline-none focus:ring-4 focus:ring-emerald-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Thinking…" : "Send"}
              </button>
            </div>
            {!docId && (
              <p className="mt-2 text-xs text-rose-600">
                Missing <code>doc_id</code> in the URL. Return to upload page and continue again.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({
  role,
  content,
  citations,
}: {
  role: "user" | "assistant";
  content: string;
  citations?: Array<{ chunk_id: number; page?: number; preview?: string }>;
}) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={[
          "max-w-[85%] rounded-2xl px-4 py-3 shadow-sm ring-1",
          isUser
            ? "bg-emerald-600 text-white ring-emerald-600/20"
            : "bg-emerald-50 text-emerald-900 ring-emerald-100",
        ].join(" ")}
      >
        <p className="whitespace-pre-wrap text-sm leading-relaxed">{content}</p>

        {citations && citations.length > 0 && (
          <div className="mt-3 grid gap-2">
            <div className="text-xs font-semibold opacity-70">Citations</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {citations.map((c, idx) => (
                <div
                  key={`${c.chunk_id}-${idx}`}
                  className="rounded-md bg-white/60 ring-1 ring-emerald-100 p-2 text-xs"
                  title={c.preview || ""}
                >
                  <span className="font-medium">Chunk #{c.chunk_id}</span>
                  {typeof c.page !== "undefined" && (
                    <span className="ml-2 opacity-70">Page {c.page}</span>
                  )}
                  {c.preview && <p className="mt-1 line-clamp-2 opacity-80">{c.preview}</p>}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
