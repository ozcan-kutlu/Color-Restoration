import { NextRequest, NextResponse } from "next/server";

/** Vercel: renklendirme + ağ gecikmesi için (planınıza göre üst sınır değişir). */
export const maxDuration = 60;

const DEFAULT_BACKEND = "http://127.0.0.1:8000";

function backendBaseUrl(): string {
  const url = process.env.COLOR_RESTORATION_API_URL?.trim();
  return url && url.length > 0 ? url.replace(/\/$/, "") : DEFAULT_BACKEND;
}

export async function POST(request: NextRequest) {
  let formData: FormData;
  try {
    formData = await request.formData();
  } catch {
    return NextResponse.json(
      { error: "Geçersiz istek gövdesi." },
      { status: 400 },
    );
  }

  const file = formData.get("file");
  if (!file || !(file instanceof File) || file.size === 0) {
    return NextResponse.json(
      { error: "Lütfen bir görsel dosyası yükleyin." },
      { status: 400 },
    );
  }

  const allowed = new Set([
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
  ]);
  if (file.type && !allowed.has(file.type)) {
    return NextResponse.json(
      { error: "Desteklenen türler: PNG, JPEG, WebP." },
      { status: 415 },
    );
  }

  const backendForm = new FormData();
  backendForm.append("file", file, file.name);

  let upstream: Response;
  try {
    upstream = await fetch(
      `${backendBaseUrl()}/api/v1/images/colorize`,
      {
        method: "POST",
        body: backendForm,
      },
    );
  } catch {
    return NextResponse.json(
      {
        error:
          "Backend’e bağlanılamadı. API’nin çalıştığından ve COLOR_RESTORATION_API_URL ayarının doğru olduğundan emin olun.",
      },
      { status: 502 },
    );
  }

  if (!upstream.ok) {
    let detail = `Sunucu hatası (${upstream.status}).`;
    try {
      const text = await upstream.text();
      if (text) {
        try {
          const j = JSON.parse(text) as { detail?: unknown };
          if (typeof j.detail === "string") detail = j.detail;
          else if (Array.isArray(j.detail) && j.detail[0]?.msg)
            detail = String(j.detail[0].msg);
        } catch {
          if (text.length < 300) detail = text;
        }
      }
    } catch {
      /* ignore */
    }
    return NextResponse.json({ error: detail }, { status: upstream.status });
  }

  const buffer = await upstream.arrayBuffer();
  const contentType =
    upstream.headers.get("Content-Type") ?? "image/png";

  return new NextResponse(buffer, {
    status: 200,
    headers: {
      "Content-Type": contentType,
      "Cache-Control": "no-store",
    },
  });
}
