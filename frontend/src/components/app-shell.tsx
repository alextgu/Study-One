"use client";

import { type ReactNode } from "react";
import { Header } from "./header";
import { AuthPrompt } from "./auth-prompt";
import { StickerBackground } from "./sticker-background";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <>
      <StickerBackground />
      <div className="relative z-[1]">
        <Header />
        <AuthPrompt />
        {children}
      </div>
    </>
  );
}
