# AI Notes Summary – Frontend Implementation Checklist

> One‑page, copy‑paste friendly plan.
> Legend: 🟩 = already implemented, ⬜ = to implement

---

## 0) Project Setup & Config

* 🟩 **TypeScript & Vite** – React + TS template initialized (`npm create vite@latest`).
* 🟩 **Dependencies** – Installed `axios`, `tailwindcss`, `postcss`, `autoprefixer`.
* 🟩 **Tailwind** – Config files (`tailwind.config.js`, `postcss.config.js`) created; directives added to CSS; dev server running with utility classes.
* 🟩 **Proxy** – `vite.config.ts` proxies `/upload` and `/query` to `http://localhost:5000`.

**Done criteria:** Dev server starts (`npm run dev`); Tailwind classes apply; API calls route via proxy.

---

## 1) API Layer

* 🟩 **`src/api.ts`**

  * `uploadPdf(file: File, docName?: string)` – multipart POST to `/upload`.
  * ⬜ `queryApi(docId: number, question: string)` – JSON POST to `/query`, returns answer + citations.

**Done criteria:** `uploadPdf` returns correct JSON; `queryApi` stub returns expected shape.

---

## 2) Layout Components

* 🟩 **`Header.tsx`** – Simple header with app title.
* 🟩 **`Footer.tsx`** – Minimal footer with copyright.
* 🟩 **`App.tsx`** – Arranges `<Header />`, `<UploadForm />`, and `<Footer />` in flex layout.

**Done criteria:** Consistent header/footer on all pages; mobile‑responsive container.

---

## 3) Upload UI

* 🟩 **`UploadForm.tsx`** –

  * File input + optional name field.
  * Submit button disabled until file selected.
  * Shows status, `doc_id`, and `chunkCount` on success.
* 🟩 **State management** – `useState` for file, name, status, loading, docId, chunkCount.
* 🟩 **Error handling** – Displays API error messages.

**Done criteria:** Uploads PDF; displays “Upload successful, X chunks created.”

---

## 4) Query UI

* ⬜ **`QueryForm.tsx`** –

  * Text input for question; requires existing `doc_id`.
  * Submit triggers `queryApi` and displays loading state.
  * Shows answer text and list of citations (chunk IDs/pages).
* ⬜ **State management** – Store `question`, `answer`, `citations`, `loading`.
* ⬜ **Error handling** – Display validation and server errors.

**Done criteria:** Given a question, displays LLM response and citation list.

---

## 5) Styling & UX

* 🟩 **Basic styling** via Tailwind utilities.
* ⬜ **Form layout improvements** – Grid or spacing refinements.
* ⬜ **Responsive design** – Ensure forms look good on mobile.
* ⬜ **Loading indicators** – Spinners or skeletons for upload & query.

**Done criteria:** Clean, user-friendly forms with clear feedback.

---

## 6) Future Enhancements

* ⬜ **Navigation** – Switch between upload and query views.
* ⬜ **History** – Save/upload logs of past `doc_id` and queries.
* ⬜ **Authentication** – Protect endpoints if needed.

**Done criteria:** Extended features roadmap documented in README.

---

## Definition of Done (Frontend)

* Upload UI fully functional end‑to‑end (PDF → chunk response).
* Query UI implemented and integrated with backend.
* Responsive, styled forms with clear error/success states.
* README updated with usage instructions and environment variables.
