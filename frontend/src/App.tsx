// src/App.tsx

import { Header } from "./components/Header";
import { Footer } from "./components/Footer";
import { UploadForm } from "./components/UploadForm";

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-grow max-w-md w-full mx-auto p-4">
        <h1 className="text-2xl mb-4">Upload a PDF</h1>
        <UploadForm />
      </main>

      <Footer />
    </div>
  );
}
