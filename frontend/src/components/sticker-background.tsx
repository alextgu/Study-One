"use client";

import * as React from "react";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/auth-context";
import {
  getPurchasedStickerIds,
  getStickerEditMode,
  getStickerPositionOverrides,
  setStickerPositionOverride,
  STICKERS,
  STICKER_EVENT,
} from "@/lib/sticker-shop";

export function StickerBackground() {
  const { user } = useAuth();
  const pathname = usePathname();
  const isShop = pathname === "/shop";
  const [editMode, setEditMode] = React.useState(false);
  const [ids, setIds] = React.useState<string[]>([]);
  const [positions, setPositions] = React.useState<Record<string, { topPct: number; leftPct: number }>>({});
  const [draggingId, setDraggingId] = React.useState<string | null>(null);
  const dragOffsetRef = React.useRef({ dx: 0, dy: 0 });

  const refresh = React.useCallback(() => {
    setIds(getPurchasedStickerIds(user?.id ?? null));
    setPositions(getStickerPositionOverrides(user?.id ?? null));
    setEditMode(getStickerEditMode());
  }, [user?.id]);

  React.useEffect(() => {
    refresh();
    window.addEventListener(STICKER_EVENT, refresh);
    window.addEventListener("storage", refresh);
    return () => {
      window.removeEventListener(STICKER_EVENT, refresh);
      window.removeEventListener("storage", refresh);
    };
  }, [refresh]);

  const purchased = STICKERS.filter((s) => ids.includes(s.id));
  if (purchased.length === 0) return null;

  const canEdit = isShop && editMode;

  function onPointerDown(e: React.PointerEvent<HTMLDivElement>, stickerId: string) {
    if (!canEdit) return;
    const target = e.currentTarget;
    const rect = target.getBoundingClientRect();
    dragOffsetRef.current = {
      dx: e.clientX - rect.left,
      dy: e.clientY - rect.top,
    };
    target.setPointerCapture(e.pointerId);
    setDraggingId(stickerId);
  }

  function onPointerMove(e: React.PointerEvent<HTMLDivElement>, stickerId: string) {
    if (!canEdit) return;
    if (draggingId !== stickerId) return;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const leftPx = e.clientX - dragOffsetRef.current.dx;
    const topPx = e.clientY - dragOffsetRef.current.dy;
    const leftPct = (leftPx / Math.max(1, vw)) * 100;
    const topPct = (topPx / Math.max(1, vh)) * 100;
    setPositions((prev) => ({
      ...prev,
      [stickerId]: {
        leftPct: Math.max(0, Math.min(100, leftPct)),
        topPct: Math.max(0, Math.min(100, topPct)),
      },
    }));
  }

  function onPointerUp(e: React.PointerEvent<HTMLDivElement>, stickerId: string) {
    if (!canEdit) return;
    if (draggingId !== stickerId) return;
    const pos = positions[stickerId];
    if (pos) {
      setStickerPositionOverride(user?.id ?? null, stickerId, pos.topPct, pos.leftPct);
    }
    setDraggingId(null);
    e.currentTarget.releasePointerCapture(e.pointerId);
  }

  return (
    <div aria-hidden className={`pointer-events-none absolute inset-0 overflow-hidden ${canEdit ? "z-[60]" : "z-0"}`}>
      {purchased.map((s) => (
        (() => {
          const override = positions[s.id];
          const top = override ? `${override.topPct}%` : s.position.top;
          const left = override ? `${override.leftPct}%` : s.position.left;
          return (
        <div
          key={s.id}
          className={`${canEdit ? "pointer-events-auto" : "pointer-events-none"} absolute select-none rounded-md border border-black/10 bg-white/45 px-2 py-1 text-xl shadow-sm backdrop-blur-[1px]`}
          style={{
            top,
            left,
            color: s.color,
            transform: `rotate(${s.position.rotateDeg}deg) scale(${s.position.scale})`,
            cursor: canEdit ? (draggingId === s.id ? "grabbing" : "grab") : "default",
          }}
          onPointerDown={(e) => onPointerDown(e, s.id)}
          onPointerMove={(e) => onPointerMove(e, s.id)}
          onPointerUp={(e) => onPointerUp(e, s.id)}
        >
          {s.glyph}
        </div>
          );
        })()
      ))}
    </div>
  );
}

