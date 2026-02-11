import { useMutation } from "@tanstack/react-query";
import { useState, useCallback } from "react";
import { dmApi } from "@/services/api";
import type {
  GenerateDMRequest,
  GenerateDMResponse,
  ProgressUpdate,
} from "@/types";

export function useDMGeneration() {
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const [eventSource, setEventSource] = useState<EventSource | null>(null);

  // 通常の生成（非ストリーミング）
  const generateMutation = useMutation({
    mutationFn: (request: GenerateDMRequest) => dmApi.generateDM(request),
    onSuccess: () => {
      setProgress({
        stage: "completed",
        message: "生成が完了しました",
        progress: 100,
      });
    },
  });

  // ストリーミング生成
  const generateStreamMutation = useMutation({
    mutationFn: async (request: GenerateDMRequest) => {
      return new Promise<GenerateDMResponse>((resolve, reject) => {
        dmApi.generateDMStream(
          request,
          (update) => {
            setProgress({
              stage: update.stage as ProgressUpdate["stage"],
              message: update.message,
              progress: update.progress,
            });
          },
          (result) => {
            resolve(result);
            setEventSource(null);
          },
          (error) => {
            reject(error);
            setEventSource(null);
          }
        );
      });
    },
  });

  const cancelGeneration = useCallback(() => {
    if (eventSource) {
      eventSource.close();
      setEventSource(null);
      setProgress(null);
    }
  }, [eventSource]);

  return {
    // 通常生成
    generateDM: generateMutation.mutate,
    generateDMAsync: generateMutation.mutateAsync,
    isGenerating: generateMutation.isPending,
    generateError: generateMutation.error,

    // ストリーミング生成
    generateDMStream: generateStreamMutation.mutate,
    generateDMStreamAsync: generateStreamMutation.mutateAsync,
    isStreaming: generateStreamMutation.isPending,
    streamError: generateStreamMutation.error,

    // 進捗
    progress,
    cancelGeneration,
  };
}
