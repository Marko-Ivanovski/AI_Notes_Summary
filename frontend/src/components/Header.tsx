// src/components/Header.tsx

export function Header() {
  return (
    <header className="w-full bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/60 shadow-sm">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="text-lg font-semibold text-emerald-800">AI Notes App</div>
        <nav className="text-sm text-emerald-800/70">
          {/* reserved for future nav */}
        </nav>
      </div>
    </header>
  );
}
