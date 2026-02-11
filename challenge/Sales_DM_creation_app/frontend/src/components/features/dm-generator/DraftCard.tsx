"use client";

import { DMDraft } from "@/types";
import { Clipboard, ClipboardCheck, Sparkles } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

const toneLabel: Record<DMDraft["tone"], string> = {
  polite: "礼儀正しい",
  casual: "カジュアル",
  problem_solver: "課題解決型",
};

const toneColors: Record<DMDraft["tone"], string> = {
  polite: "blue",
  casual: "emerald",
  problem_solver: "purple",
};

type Props = {
  draft: DMDraft;
  onEdit?: (editedBody: string) => void;
};

export function DraftCard({ draft, onEdit }: Props) {
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedBody, setEditedBody] = useState(draft.body_markdown);

  const handleCopy = async () => {
    const text = `${draft.title}\n\n${isEditing ? editedBody : draft.body_markdown}`;
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSave = () => {
    if (onEdit) {
      onEdit(editedBody);
    }
    setIsEditing(false);
  };

  const colorClass = toneColors[draft.tone];

  return (
    <Card className="flex flex-col hover:border-primary/50 transition-all duration-200">
      <CardHeader className="pb-3 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className={cn(
                "h-7 w-7 rounded-lg flex items-center justify-center border",
                colorClass === "blue" && "bg-blue-500/20 border-blue-500/30",
                colorClass === "emerald" &&
                  "bg-emerald-500/20 border-emerald-500/30",
                colorClass === "purple" &&
                  "bg-purple-500/20 border-purple-500/30"
              )}
            >
              <Sparkles
                className={cn(
                  "h-3.5 w-3.5",
                  colorClass === "blue" && "text-blue-400",
                  colorClass === "emerald" && "text-emerald-400",
                  colorClass === "purple" && "text-purple-400"
                )}
              />
            </div>
            <div>
              <span className="text-[10px] text-muted-foreground block">トーン</span>
              <p className="text-sm font-semibold">{toneLabel[draft.tone]}</p>
            </div>
          </div>
          <Button
            onClick={handleCopy}
            variant={copied ? "default" : "outline"}
            size="sm"
            className="h-8"
          >
            {copied ? (
              <>
                <ClipboardCheck className="h-3.5 w-3.5 mr-1.5" />
                コピー済み
              </>
            ) : (
              <>
                <Clipboard className="h-3.5 w-3.5 mr-1.5" />
                コピー
              </>
            )}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="flex-1 overflow-y-auto custom-scrollbar min-h-0 pt-4">
        {isEditing ? (
          <div className="space-y-3">
            <div>
              <h3 className="text-base font-semibold mb-2">{draft.title}</h3>
              <Textarea
                value={editedBody}
                onChange={(e) => setEditedBody(e.target.value)}
                className="min-h-[200px] font-mono text-sm"
              />
            </div>
            <div className="flex gap-2">
              <Button onClick={handleSave} size="sm">
                保存
              </Button>
              <Button
                onClick={() => {
                  setIsEditing(false);
                  setEditedBody(draft.body_markdown);
                }}
                variant="outline"
                size="sm"
              >
                キャンセル
              </Button>
            </div>
          </div>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown>{`## ${draft.title}\n\n${draft.body_markdown}`}</ReactMarkdown>
            <Button
              onClick={() => setIsEditing(true)}
              variant="ghost"
              size="sm"
              className="mt-4 w-full"
            >
              編集
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
