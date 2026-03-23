"use client";

import * as React from "react";
import Link from "next/link";
import { useAuth } from "@/context/auth-context";
import { fetchStudyDashboardAnalytics } from "@/lib/study-analytics";
import {
  getStickerEditMode,
  getPurchasedStickerIds,
  getSpentPoints,
  setStickerEditMode,
  setPurchasedStickerIds,
  STICKERS,
} from "@/lib/sticker-shop";

export default function ShopPage() {
  const { user, loading: authLoading } = useAuth();
  const [points, setPoints] = React.useState(0);
  const [pointsLoading, setPointsLoading] = React.useState(true);
  const [owned, setOwned] = React.useState<string[]>([]);
  const [editMode, setEditModeState] = React.useState(false);

  React.useEffect(() => {
    setOwned(getPurchasedStickerIds(user?.id ?? null));
    setEditModeState(getStickerEditMode());
  }, [user?.id]);

  React.useEffect(() => {
    if (!user) {
      setPoints(0);
      setPointsLoading(false);
      return;
    }
    let cancelled = false;
    setPointsLoading(true);
    fetchStudyDashboardAnalytics(user.id)
      .then((d) => {
        if (!cancelled) setPoints(d.totalXp);
      })
      .catch(() => {
        if (!cancelled) setPoints(0);
      })
      .finally(() => {
        if (!cancelled) setPointsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [user]);

  const spent = React.useMemo(() => getSpentPoints(owned), [owned]);
  const available = Math.max(0, points - spent);

  function buySticker(id: string, cost: number) {
    if (!user) return;
    if (owned.includes(id)) return;
    if (available < cost) return;
    const next = [...owned, id];
    setOwned(next);
    setPurchasedStickerIds(user.id, next);
  }

  function toggleEditMode() {
    const next = !editMode;
    setStickerEditMode(next);
    setEditModeState(next);
  }

  return (
    <main className="min-h-screen p-4 sm:p-6">
      <div className="mx-auto w-full max-w-5xl space-y-6">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold">Sticker shop</h1>
          <p className="text-sm text-muted-foreground">
            Buy placeholder stickers with your XP points. Purchased stickers are placed on your app
            background and stay there in this browser.
          </p>
        </header>

        <section className="rounded-lg border border-border bg-card p-4 shadow-sm sm:p-5">
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <span className="rounded-md border border-border bg-background px-3 py-1.5">
              Total XP: <strong>{pointsLoading ? "…" : points.toLocaleString()}</strong>
            </span>
            <span className="rounded-md border border-border bg-background px-3 py-1.5">
              Spent: <strong>{spent.toLocaleString()}</strong>
            </span>
            <span className="rounded-md border border-border bg-background px-3 py-1.5">
              Available: <strong>{available.toLocaleString()}</strong>
            </span>
            <button
              type="button"
              onClick={toggleEditMode}
              className={`rounded-md border px-3 py-1.5 text-xs font-medium ${
                editMode
                  ? "border-emerald-600 bg-emerald-600/10 text-emerald-700"
                  : "border-border bg-background hover:bg-muted"
              }`}
            >
              {editMode ? "Done editing stickers" : "Edit sticker layout"}
            </button>
          </div>
          {!authLoading && !user && (
            <p className="mt-3 text-sm text-muted-foreground">
              Sign in to buy stickers with your points.
            </p>
          )}
          {editMode && (
            <p className="mt-3 text-xs text-muted-foreground">
              Edit mode is on: drag stickers directly on the page background, then click
              <strong className="text-foreground"> Done editing stickers</strong>.
            </p>
          )}
        </section>

        {!editMode && (
          <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {STICKERS.map((sticker) => {
              const isOwned = owned.includes(sticker.id);
              const canBuy = !!user && available >= sticker.cost && !isOwned;
              return (
                <article
                  key={sticker.id}
                  className="rounded-lg border border-border bg-card p-4 text-card-foreground shadow-sm"
                >
                  <div className="mb-3 flex items-center justify-between">
                    <h2 className="font-medium">{sticker.name}</h2>
                    <span className="text-xs text-muted-foreground">{sticker.cost} XP</span>
                  </div>
                  <div className="mb-4 flex h-24 items-center justify-center rounded-md border border-dashed border-border bg-muted/20">
                    <span
                      className="select-none text-4xl"
                      style={{ color: sticker.color }}
                      aria-hidden
                    >
                      {sticker.glyph}
                    </span>
                  </div>
                  <button
                    type="button"
                    disabled={!canBuy}
                    onClick={() => buySticker(sticker.id, sticker.cost)}
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm font-medium hover:bg-muted disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {isOwned ? "Owned (on background)" : canBuy ? "Buy sticker" : "Not enough points"}
                  </button>
                </article>
              );
            })}
          </section>
        )}

        {!editMode && (
          <Link href="/profile" className="inline-block text-sm text-muted-foreground underline hover:text-foreground">
            ← Back to profile
          </Link>
        )}
      </div>
    </main>
  );
}

