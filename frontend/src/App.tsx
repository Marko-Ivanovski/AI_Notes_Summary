// src/App.tsx

import { Header } from "./components/Header";
import { Footer } from "./components/Footer";
import { UploadForm } from "./components/UploadForm";

export default function App() {
  return (
    <div className="min-h-screen w-full flex flex-col bg-emerald-50">
      <Header />

      {/* Center the whole upload card and give it room */}
      <main className="flex-1 flex items-center justify-center px-6 py-12">
        {/* Optional page title (style matches the card theme) */}
        <div className="w-full">
          <h1 className="sr-only">Upload a PDF</h1>
          <UploadForm />
        </div>
      </main>

      <Footer />
    </div>
  );
}
