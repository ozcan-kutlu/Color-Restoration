"use client";

/* blob önizleme URL’leri için <img> gerekli */
/* eslint-disable @next/next/no-img-element */

import { useCallback, useEffect, useId, useRef, useState } from "react";

const ACCEPT = "image/png,image/jpeg,image/jpg,image/webp";
const MAX_FILE_SIZE_MB = 8;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

function formatMb(sizeBytes: number): string {
  return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
}

function revokeIfNeeded(url: string | null) {
  if (url?.startsWith("blob:")) URL.revokeObjectURL(url);
}

export function ColorizePanel() {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  const resetOutput = useCallback(() => {
    setResultUrl((prev) => {
      revokeIfNeeded(prev);
      return null;
    });
    setError(null);
  }, []);

  const setChosenFile = useCallback(
    (next: File | null) => {
      setFile(next);
      setPreviewUrl((prev) => {
        revokeIfNeeded(prev);
        if (!next) return null;
        return URL.createObjectURL(next);
      });
      resetOutput();
    },
    [resetOutput],
  );

  useEffect(() => {
    return () => {
      revokeIfNeeded(previewUrl);
      revokeIfNeeded(resultUrl);
    };
  }, [previewUrl, resultUrl]);

  const onFiles = useCallback(
    (list: FileList | null) => {
      if (!list?.length) return;
      const f = list[0];
      if (!f.type.startsWith("image/")) {
        setError("Lütfen bir görsel dosyası seçin.");
        return;
      }
      if (f.size > MAX_FILE_SIZE_BYTES) {
        setError(
          `Dosya çok büyük (${formatMb(f.size)}). En fazla ${MAX_FILE_SIZE_MB} MB yükleyebilirsiniz. Daha küçük bir görsel deneyin.`,
        );
        return;
      }
      setChosenFile(f);
    },
    [setChosenFile],
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      onFiles(e.dataTransfer.files);
    },
    [onFiles],
  );

  const onSubmit = async () => {
    if (!file) {
      setError("Önce bir görsel yükleyin.");
      return;
    }
    setLoading(true);
    setError(null);
    setResultUrl((prev) => {
      revokeIfNeeded(prev);
      return null;
    });

    const body = new FormData();
    body.append("file", file, file.name);

    try {
      const res = await fetch("/api/colorize", {
        method: "POST",
        body,
      });

      if (!res.ok) {
        const ct = res.headers.get("Content-Type") ?? "";
        if (ct.includes("application/json")) {
          const j = (await res.json()) as { error?: string };
          setError(j.error ?? "İşlem başarısız.");
        } else {
          setError(`Hata (${res.status}).`);
        }
        return;
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setResultUrl(url);
    } catch {
      setError("Ağ hatası. Bağlantınızı kontrol edin.");
    } finally {
      setLoading(false);
    }
  };

  const clearAll = () => {
    setFile(null);
    setPreviewUrl((prev) => {
      revokeIfNeeded(prev);
      return null;
    });
    setResultUrl((prev) => {
      revokeIfNeeded(prev);
      return null;
    });
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const downloadResult = () => {
    if (!resultUrl || !file) return;
    const a = document.createElement("a");
    a.href = resultUrl;
    const base = file.name.replace(/\.[^.]+$/, "") || "gorsel";
    a.download = `${base}-renkli.png`;
    a.click();
  };

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-8 px-4 pb-16 pt-6 sm:px-6">
      <div
        role="button"
        tabIndex={0}
        onDragEnter={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        className={[
          "group relative cursor-pointer rounded-2xl border-2 border-dashed transition-colors",
          dragOver
            ? "border-amber-400/80 bg-amber-500/10"
            : "border-zinc-600/80 bg-zinc-900/40 hover:border-zinc-500 hover:bg-zinc-900/60",
        ].join(" ")}
      >
        <input
          ref={inputRef}
          id={inputId}
          type="file"
          accept={ACCEPT}
          className="sr-only"
          onChange={(e) => onFiles(e.target.files)}
        />
        <label
          htmlFor={inputId}
          className="flex min-h-[200px] cursor-pointer flex-col items-center justify-center gap-3 px-6 py-12 text-center"
        >
          <span className="flex h-14 w-14 items-center justify-center rounded-full bg-zinc-800 text-2xl text-amber-400/90 ring-1 ring-zinc-700">
            ↑
          </span>
          <span className="text-lg font-medium text-zinc-100">
            Görseli sürükleyip bırakın veya seçin
          </span>
          <span className="max-w-sm text-sm text-zinc-500">
            PNG, JPEG veya WebP. En fazla {MAX_FILE_SIZE_MB} MB. Daha büyük
            dosyalarda sunucu tarafı işlem başarısız olabilir.
          </span>
          {file && (
            <span className="mt-2 rounded-full bg-zinc-800 px-4 py-1 text-sm text-zinc-300 ring-1 ring-zinc-700">
              {file.name}
            </span>
          )}
        </label>
      </div>

      {error && (
        <div
          role="alert"
          className="rounded-xl border border-red-500/40 bg-red-950/40 px-4 py-3 text-sm text-red-200"
        >
          {error}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={onSubmit}
          disabled={loading || !file}
          className="inline-flex min-h-11 items-center justify-center rounded-xl bg-amber-500 px-6 text-sm font-semibold text-zinc-950 shadow-lg shadow-amber-500/20 transition hover:bg-amber-400 disabled:pointer-events-none disabled:opacity-40"
        >
          {loading ? "Renklendiriliyor…" : "Renklendir"}
        </button>
        <button
          type="button"
          onClick={clearAll}
          disabled={loading}
          className="inline-flex min-h-11 items-center justify-center rounded-xl border border-zinc-600 bg-zinc-900/60 px-5 text-sm font-medium text-zinc-200 hover:bg-zinc-800 disabled:opacity-40"
        >
          Temizle
        </button>
        <button
          type="button"
          onClick={downloadResult}
          disabled={!resultUrl || loading}
          className="inline-flex min-h-11 items-center justify-center rounded-xl border border-amber-500/40 bg-transparent px-5 text-sm font-medium text-amber-400/95 hover:bg-amber-500/10 disabled:pointer-events-none disabled:opacity-40"
        >
          Sonucu indir (PNG)
        </button>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">
            Orijinal
          </h2>
          <div className="relative aspect-[4/3] overflow-hidden rounded-2xl bg-zinc-900 ring-1 ring-zinc-800">
            {previewUrl ? (
              <img
                src={previewUrl}
                alt="Yüklenen önizleme"
                className="h-full w-full object-contain"
              />
            ) : (
              <div className="flex h-full items-center justify-center p-6 text-center text-sm text-zinc-600">
                Henüz görsel yok
              </div>
            )}
          </div>
        </section>
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">
            Renklendirilmiş
          </h2>
          <div className="relative aspect-[4/3] overflow-hidden rounded-2xl bg-zinc-900 ring-1 ring-zinc-800">
            {resultUrl ? (
              <img
                src={resultUrl}
                alt="Renklendirilmiş sonuç"
                className="h-full w-full object-contain"
              />
            ) : (
              <div className="flex h-full items-center justify-center p-6 text-center text-sm text-zinc-600">
                {loading
                  ? "Model çalışıyor, lütfen bekleyin…"
                  : "Sonuç burada görünecek"}
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
