"use client";

import { ProgressUpdate } from "@/types";
import { Loader2, Search, Brain, PenTool } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type Props = {
  progress: ProgressUpdate | null;
};

const stageIcons = {
  researching: Search,
  analyzing: Brain,
  writing: PenTool,
  completed: Loader2,
};

const stageLabels = {
  researching: "調査中",
  analyzing: "分析中",
  writing: "執筆中",
  completed: "完了",
};

export function ProgressIndicator({ progress }: Props) {
  if (!progress) return null;

  const Icon = stageIcons[progress.stage];

  return (
    <Card className="mb-4">
      <CardContent className="pt-6">
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-primary/20 flex items-center justify-center border border-primary/30">
              <Icon
                className={cn(
                  "h-5 w-5",
                  progress.stage === "completed"
                    ? "text-primary"
                    : "text-primary animate-spin"
                )}
              />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium">{stageLabels[progress.stage]}</p>
              <p className="text-xs text-muted-foreground">{progress.message}</p>
            </div>
            <span className="text-sm font-semibold">{progress.progress}%</span>
          </div>
          <Progress value={progress.progress} className="h-2" />
        </div>
      </CardContent>
    </Card>
  );
}
