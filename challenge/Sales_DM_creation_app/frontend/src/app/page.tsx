"use client";

import { FormEvent, useState } from "react";
import { EvidenceItem, HookItem, DMDraft, ToneType } from "@/types";
import { EvidenceList } from "@/components/features/dm-generator/EvidenceList";
import { DraftCard } from "@/components/features/dm-generator/DraftCard";
import { ProgressIndicator } from "@/components/features/dm-generator/ProgressIndicator";
import { useDMGeneration } from "@/hooks/useDMGeneration";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Sparkles, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

const DEFAULT_TONES: ToneType[] = ["polite", "casual", "problem_solver"];

export default function HomePage() {
  const [targetUrl, setTargetUrl] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [productName, setProductName] = useState("");
  const [productSummary, setProductSummary] = useState("");

  const [evidences, setEvidences] = useState<EvidenceItem[]>([]);
  const [hooks, setHooks] = useState<HookItem[]>([]);
  const [drafts, setDrafts] = useState<DMDraft[]>([]);
  const [selectedHookIds, setSelectedHookIds] = useState<number[]>([]);

  const {
    generateDMAsync,
    isGenerating,
    generateError,
  } = useDMGeneration();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    try {
      const result = await generateDMAsync({
        target_url: targetUrl,
        target_role: targetRole || null,
        company_name: companyName || null,
        your_product_name: productName,
        your_product_summary: productSummary,
        preferred_tones: DEFAULT_TONES,
      });

      setEvidences(result.evidences || []);
      setHooks(result.hooks || []);
      setDrafts(result.drafts || []);
      setSelectedHookIds((result.hooks || []).map((h: HookItem) => h.id));
    } catch (error) {
      // Error is handled by TanStack Query
      console.error("Generation failed:", error);
    }
  };

  const handleToggleHook = (hookId: number) => {
    setSelectedHookIds((prev) =>
      prev.includes(hookId)
        ? prev.filter((id) => id !== hookId)
        : [...prev, hookId]
    );
  };

  const handleDraftEdit = (index: number, editedBody: string) => {
    setDrafts((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], body_markdown: editedBody };
      return updated;
    });
  };

  return (
    <div className="container mx-auto px-4 md:px-6 py-6 flex flex-col gap-4 max-w-[1920px]">
      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle>DM生成フォーム</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              {/* Target URL */}
              <div className="lg:col-span-4 space-y-2">
                <label className="text-sm font-medium flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary"></span>
                  相手の URL <span className="text-destructive">*</span>
                </label>
                <Input
                  type="url"
                  required
                  placeholder="https://example.com"
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                />
              </div>

              {/* Target Info */}
              <div className="lg:col-span-4 space-y-2">
                <label className="text-sm font-medium flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-blue-500"></span>
                  ターゲット情報（任意）
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    type="text"
                    placeholder="例: VP of Sales"
                    value={targetRole}
                    onChange={(e) => setTargetRole(e.target.value)}
                  />
                  <Input
                    type="text"
                    placeholder="会社名"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                  />
                </div>
              </div>

              {/* Product Info */}
              <div className="lg:col-span-4 space-y-2">
                <label className="text-sm font-medium flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-purple-500"></span>
                  あなたの商材情報 <span className="text-destructive">*</span>
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    type="text"
                    required
                    placeholder="商材名"
                    value={productName}
                    onChange={(e) => setProductName(e.target.value)}
                  />
                  <Input
                    type="text"
                    required
                    placeholder="一文で要約"
                    value={productSummary}
                    onChange={(e) => setProductSummary(e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* Progress & Error */}
            {isGenerating && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground bg-muted/50 border rounded-lg p-3">
                <Sparkles className="h-4 w-4 animate-pulse" />
                <span>DMを生成中です。しばらくお待ちください...</span>
              </div>
            )}
            {generateError && (
              <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-lg p-3">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{generateError.message || "エラーが発生しました"}</span>
              </div>
            )}

            {/* Submit Button */}
            <div className="flex items-center justify-between pt-2">
              <div className="flex-1"></div>
              <Button
                type="submit"
                disabled={isGenerating}
                className={cn(
                  "min-w-[160px]",
                  isGenerating && "opacity-60 cursor-not-allowed"
                )}
              >
                {isGenerating ? (
                  <>
                    <Sparkles className="h-4 w-4 mr-2 animate-pulse" />
                    生成中...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    AI で DM を生成
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* 2 Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,1.3fr)] gap-4 flex-1 min-h-[500px]">
        {/* Left: Evidence & Hooks */}
        <div className="h-full min-h-[400px]">
          <EvidenceList
            evidences={evidences}
            hooks={hooks}
            selectedHookIds={selectedHookIds}
            onToggleHook={handleToggleHook}
          />
        </div>

        {/* Right: Drafts */}
        <Card className="h-full min-h-[400px] flex flex-col">
          <CardHeader className="border-b">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary/20 to-primary/30 border border-primary/30 flex items-center justify-center">
                  <Sparkles className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <CardTitle className="text-base">生成された DM 案</CardTitle>
                  <p className="text-xs text-muted-foreground">
                    3つのトーンで生成（Markdown形式）
                  </p>
                </div>
              </div>
              {drafts.length > 0 && (
                <span className="text-xs text-muted-foreground px-2 py-1 rounded bg-muted border">
                  {drafts.length}件
                </span>
              )}
            </div>
          </CardHeader>
          <CardContent className="flex-1 overflow-y-auto custom-scrollbar min-h-0 pt-6">
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-3">
              {drafts.map((draft, i) => (
                <DraftCard
                  key={i}
                  draft={draft}
                  onEdit={(editedBody) => handleDraftEdit(i, editedBody)}
                />
              ))}
              {drafts.length === 0 && (
                <div className="col-span-3 flex flex-col items-center justify-center text-center py-16 border border-dashed rounded-xl bg-muted/30">
                  <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center mb-4">
                    <Sparkles className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <p className="text-sm text-muted-foreground mb-1">
                    ここに AI が生成した営業 DM 案が表示されます
                  </p>
                  <p className="text-xs text-muted-foreground">
                    フォームに入力して「AI で DM を生成」をクリックしてください
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
