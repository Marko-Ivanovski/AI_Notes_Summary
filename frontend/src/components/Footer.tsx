// src/components/Footer.tsx

export function Footer() {
  return (
    <footer className="w-full bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/60 border-t border-emerald-100">
      <div className="max-w-6xl mx-auto px-6 py-6 text-center text-sm text-emerald-800">
        © {new Date().getFullYear()} Marko Ivanovski
      </div>
    </footer>
  );
}
