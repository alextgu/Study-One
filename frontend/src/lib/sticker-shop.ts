export type StickerDef = {
  id: string;
  name: string;
  cost: number;
  color: string;
  glyph: string;
  position: { top: string; left: string; rotateDeg: number; scale: number };
};

const PREFIX = "socrato-sticker-shop-v1";
const LAYOUT_PREFIX = "socrato-sticker-layout-v1";
const EDIT_MODE_KEY = "socrato-sticker-edit-mode-v1";
export const STICKER_EVENT = "socrato-stickers-updated";

export const STICKERS: StickerDef[] = [
  { id: "test-debug", name: "Test Debug", cost: 0, color: "#ef4444", glyph: "🧪", position: { top: "8%", left: "46%", rotateDeg: 0, scale: 1.1 } },
  { id: "star-burst", name: "Star Burst", cost: 40, color: "#facc15", glyph: "★", position: { top: "18%", left: "8%", rotateDeg: -8, scale: 1 } },
  { id: "spark-note", name: "Spark Note", cost: 55, color: "#60a5fa", glyph: "✦", position: { top: "26%", left: "80%", rotateDeg: 10, scale: 1 } },
  { id: "pixel-heart", name: "Pixel Heart", cost: 75, color: "#fb7185", glyph: "♥", position: { top: "66%", left: "12%", rotateDeg: -6, scale: 1.05 } },
  { id: "bolt-tag", name: "Bolt Tag", cost: 95, color: "#a78bfa", glyph: "⚡", position: { top: "74%", left: "84%", rotateDeg: 9, scale: 1.1 } },
  { id: "leaf-badge", name: "Leaf Badge", cost: 65, color: "#4ade80", glyph: "✿", position: { top: "44%", left: "6%", rotateDeg: -12, scale: 1 } },
  { id: "moon-chip", name: "Moon Chip", cost: 85, color: "#94a3b8", glyph: "☾", position: { top: "12%", left: "62%", rotateDeg: 6, scale: 1 } },
];

function keyFor(userId: string | null) {
  return `${PREFIX}:${userId ?? "guest"}`;
}

export function getPurchasedStickerIds(userId: string | null): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(keyFor(userId));
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((v) => typeof v === "string") : [];
  } catch {
    return [];
  }
}

export function setPurchasedStickerIds(userId: string | null, ids: string[]) {
  if (typeof window === "undefined") return;
  localStorage.setItem(keyFor(userId), JSON.stringify(ids));
  window.dispatchEvent(new Event(STICKER_EVENT));
}

export function getSpentPoints(ids: string[]) {
  return ids.reduce((sum, id) => {
    const s = STICKERS.find((x) => x.id === id);
    return sum + (s?.cost ?? 0);
  }, 0);
}

export function addTestSticker(userId: string | null) {
  const ids = getPurchasedStickerIds(userId);
  if (ids.includes("test-debug")) return ids;
  const next = [...ids, "test-debug"];
  setPurchasedStickerIds(userId, next);
  return next;
}

function layoutKeyFor(userId: string | null) {
  return `${LAYOUT_PREFIX}:${userId ?? "guest"}`;
}

export type StickerPositionOverrides = Record<string, { topPct: number; leftPct: number }>;

export function getStickerPositionOverrides(userId: string | null): StickerPositionOverrides {
  if (typeof window === "undefined") return {};
  try {
    const raw = localStorage.getItem(layoutKeyFor(userId));
    if (!raw) return {};
    const parsed = JSON.parse(raw) as StickerPositionOverrides;
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

export function setStickerPositionOverride(
  userId: string | null,
  stickerId: string,
  topPct: number,
  leftPct: number,
) {
  if (typeof window === "undefined") return;
  const current = getStickerPositionOverrides(userId);
  current[stickerId] = {
    topPct: Math.max(0, Math.min(100, topPct)),
    leftPct: Math.max(0, Math.min(100, leftPct)),
  };
  localStorage.setItem(layoutKeyFor(userId), JSON.stringify(current));
  window.dispatchEvent(new Event(STICKER_EVENT));
}

export function getStickerEditMode(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(EDIT_MODE_KEY) === "1";
}

export function setStickerEditMode(enabled: boolean) {
  if (typeof window === "undefined") return;
  localStorage.setItem(EDIT_MODE_KEY, enabled ? "1" : "0");
  window.dispatchEvent(new Event(STICKER_EVENT));
}

