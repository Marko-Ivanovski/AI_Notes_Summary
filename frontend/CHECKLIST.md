# AI Notes Summary – Frontend Implementation Checklist

> One‑page, copy‑paste friendly plan.
> Legend: 🟩 = already implemented, ⬜ = to implement

---

## 0) Project Setup & Config

* 🟩 **TypeScript & Vite** – React + TS template initialized.
* 🟩 **Dependencies** – Installed `axios`, `tailwindcss`, `postcss`, `autoprefixer`.
* 🟩 **Tailwind** – Configured; directives added; styling works.
* 🟩 **Proxy** – `vite.config.ts` proxies `/upload` and `/query` to backend.

**Done criteria:** Dev server runs; API calls routed.

---

## 1) API Layer

* 🟩 **`uploadPdf(file, docName?)`** – multipart POST to `/upload`, returns `doc_id` and `chunks` count.
* 🟩 **`fetchChunks(docId)`** – GET `/chunks/:doc_id`, returns chunk previews.

**Done criteria:** Upload and chunk listing work; query layer stub ready.

---

## 2) Layout Components

* 🟩 **`Header.tsx`**, **`Footer.tsx`**, **`App.tsx`** – Basic layout with header, main, footer.

**Done criteria:** Consistent UI shell.

---

## 3) Upload UI

* 🟩 **`UploadForm.tsx`** – File/name inputs, upload button, displays `doc_id`, `chunkCount`, and chunk previews list.
* 🟩 **State management** – `useState` for file, name, status, loading, docId, chunkCount, chunkList.
* 🟩 **Error handling** – Shows errors from API.

**Done criteria:** End‑to‑end PDF ingestion UI.

---

## 4) Query UI

* ⬜ **`QueryForm.tsx`** – Input for question, submits to `queryApi`, displays answer and citations.
* ⬜ **State management** – Manage `question`, `answer`, `citations`, `loading`.
* ⬜ **Error handling** – Display validation/server errors.

**Done criteria:** Q&A interface functional.

---

## 5) Styling & UX

* 🟩 **Tailwind utilities** – Basic styling applied.
* ⬜ **Responsive layout** – Ensure mobile support.
* ⬜ **Loading indicators** – Spinners for upload & query.

**Done criteria:** Polished, responsive forms.

---

## 6) Future Enhancements

* ⬜ **Navigation** – Multi-page views for upload vs query.
* ⬜ **History/Docs list** – Show uploaded documents.
* ⬜ **Authentication** – Protect backend endpoints.

**Done criteria:** Roadmap outlined.

---

## Definition of Done (Frontend)

* Upload UI + chunk preview complete.
* Query UI to be implemented.
* Responsive, styled, error‑aware forms.
