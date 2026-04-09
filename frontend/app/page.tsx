import { ColorizePanel } from "./components/ColorizePanel";

export default function Home() {
  return (
    <div className="relative flex min-h-full flex-1 flex-col">
      <div
        className="pointer-events-none absolute inset-0 opacity-40"
        aria-hidden
        style={{
          background:
            "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(245, 158, 11, 0.18), transparent), radial-gradient(ellipse 60% 40% at 100% 50%, rgba(120, 113, 198, 0.12), transparent)",
        }}
      />
      <header className="relative z-10 border-b border-zinc-800/80 bg-zinc-950/80 px-4 py-6 backdrop-blur-md sm:px-6">
        <div className="mx-auto max-w-5xl">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-amber-500/90">
            color-restoration
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight text-zinc-50 sm:text-3xl">
            Fotoğraf renklendirme
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-zinc-400">
            Siyah-beyaz veya soluk görsellerinizi yükleyin; model renklendirilmiş
            çıktıyı PNG olarak üretir. Backend API ile konuşmak için yerel proxy
            kullanılır — CORS ayarı gerekmez.
          </p>
        </div>
      </header>
      <main className="relative z-10 flex flex-1 flex-col">
        <ColorizePanel />
      </main>
    </div>
  );
}
