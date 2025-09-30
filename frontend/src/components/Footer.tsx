// src/components/Footer.tsx

export function Footer() {
  return (
    <footer className="w-full bg-gray-100 p-4 mt-10 text-center text-sm text-gray-600">
      © {new Date().getFullYear()} Marko Ivanovski
    </footer>
  );
}
