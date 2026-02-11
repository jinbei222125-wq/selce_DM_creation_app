"use client";

import { EvidenceItem, HookItem } from "@/types";
import { Check, Plus, LinkIcon, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type Props = {
  evidences: EvidenceItem[];
  hooks: HookItem[];
  selectedHookIds: number[];
  onToggleHook: (hookId: number) => void;
};

export function EvidenceList({
  evidences,
  hooks,
  selectedHookIds,
  onToggleHook,
}: Props) {
  return (
    <div className="space-y-4 h-full flex flex-col">
      {/* Evidence Section */}
      <Card className="flex-1 flex flex-col min-h-0">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-blue-500/20 flex items-center justify-center border border-blue-500/30">
                <LinkIcon className="h-4 w-4 text-blue-400" />
              </div>
              <CardTitle className="text-base">検索で見つけた証拠</CardTitle>
            </div>
            <span className="text-xs text-muted-foreground px-2 py-1 rounded bg-muted border">
              {evidences.length}件
            </span>
          </div>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto custom-scrollbar space-y-2.5 pr-2">
          {evidences.map((ev, i) => (
            <div
              key={i}
              className="rounded-lg border bg-card p-3 space-y-2 hover:border-primary/50 transition-colors group"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="inline-flex h-6 w-6 items-center justify-center rounded-md bg-muted text-xs font-medium border">
                  {i + 1}
                </span>
                <a
                  href={ev.url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors opacity-0 group-hover:opacity-100"
                >
                  <LinkIcon className="h-3 w-3" />
                  開く
                </a>
              </div>
              <h3 className="font-semibold text-sm line-clamp-2 leading-snug">
                {ev.title}
              </h3>
              <p className="text-xs text-muted-foreground line-clamp-4 leading-relaxed">
                {ev.snippet}
              </p>
              <div className="flex items-center justify-between pt-1 border-t">
                <p className="text-[10px] text-muted-foreground">{ev.source}</p>
              </div>
            </div>
          ))}
          {evidences.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-3">
                <LinkIcon className="h-6 w-6 text-muted-foreground" />
              </div>
              <p className="text-sm text-muted-foreground max-w-[200px]">
                まだ Evidence がありません。
                <br />
                フォームから URL を指定して生成してください。
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Hooks Section */}
      <Card className="flex-1 flex flex-col min-h-0">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-purple-500/20 flex items-center justify-center border border-purple-500/30">
                <Sparkles className="h-4 w-4 text-purple-400" />
              </div>
              <CardTitle className="text-base">DM に使えるフック</CardTitle>
            </div>
            <span className="text-xs text-muted-foreground px-2 py-1 rounded bg-muted border">
              {selectedHookIds.length}/{hooks.length}
            </span>
          </div>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto custom-scrollbar space-y-2 pr-2">
          {hooks.map((hook) => {
            const selected = selectedHookIds.includes(hook.id);
            return (
              <button
                key={hook.id}
                onClick={() => onToggleHook(hook.id)}
                className={cn(
                  "w-full text-left rounded-lg border p-3 text-xs transition-all duration-200 flex items-start gap-2.5 group",
                  selected
                    ? "border-primary bg-primary/10 shadow-md shadow-primary/10"
                    : "border-border bg-card hover:border-primary/50 hover:bg-accent/50"
                )}
              >
                <span
                  className={cn(
                    "mt-0.5 inline-flex h-5 w-5 items-center justify-center rounded-md border text-[10px] transition-all shrink-0",
                    selected
                      ? "border-primary bg-primary/20 text-primary"
                      : "border-border bg-muted text-muted-foreground group-hover:border-primary/50"
                  )}
                >
                  {selected ? (
                    <Check className="h-3 w-3" />
                  ) : (
                    <Plus className="h-3 w-3" />
                  )}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-sm mb-1 leading-snug">
                    {hook.title}
                  </p>
                  <p className="text-xs text-muted-foreground line-clamp-3 leading-relaxed">
                    {hook.reason}
                  </p>
                  {hook.related_evidence_indices.length > 0 && (
                    <div className="mt-1.5 flex flex-wrap gap-1">
                      {hook.related_evidence_indices.slice(0, 3).map((idx) => (
                        <span
                          key={idx}
                          className="text-[9px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground border"
                        >
                          #{idx + 1}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </button>
            );
          })}
          {hooks.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-3">
                <Sparkles className="h-6 w-6 text-muted-foreground" />
              </div>
              <p className="text-sm text-muted-foreground max-w-[200px]">
                生成されたフックがここに表示されます。
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
