import "./globals.css";
import type { ReactNode } from "react";
import { QueryProvider } from "@/components/providers/QueryProvider";

export const metadata = {
  title: "Insight DM Master",
  description: "AI-powered personalized sales DM generation tool",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ja">
      <body className="antialiased">
        <QueryProvider>
          <div className="min-h-screen flex flex-col">
            <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
              <div className="container flex h-16 items-center justify-between px-4 md:px-6">
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-primary/20 to-primary/30 flex items-center justify-center border border-primary/30 shadow-lg shadow-primary/10">
                    <span className="text-lg font-bold text-primary">DM</span>
                  </div>
                  <div>
                    <h1 className="text-base md:text-lg font-semibold">
                      Insight DM Master
                    </h1>
                    <p className="text-xs text-muted-foreground hidden sm:block">
                      AI-powered personalized sales messaging
                    </p>
                  </div>
                </div>
                <div className="hidden md:flex items-center gap-2 text-xs text-muted-foreground">
                  <span className="px-2 py-1 rounded bg-muted border">
                    LangChain + GPT-4o
                  </span>
                </div>
              </div>
            </header>
            <main className="flex-1">{children}</main>
          </div>
        </QueryProvider>
      </body>
    </html>
  );
}
