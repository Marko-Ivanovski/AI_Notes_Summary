// src/App.tsx

import { Header } from "./components/Header";
import { Footer } from "./components/Footer";
import { UploadForm } from "./components/UploadForm";
import { Routes, Route } from "react-router-dom";
import { Chat } from "./components/Chat";

export default function App() {
  return (
    <div className="min-h-screen w-full flex flex-col bg-emerald-50">
      <Header />
      <main className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full">
          <h1 className="sr-only">Upload a PDF</h1>
          <Routes>
            <Route path="/" element={<UploadForm />} />
            <Route path="/chat" element={<Chat />} />
          </Routes>
        </div>
      </main>
      <Footer />
    </div>
  );
}
