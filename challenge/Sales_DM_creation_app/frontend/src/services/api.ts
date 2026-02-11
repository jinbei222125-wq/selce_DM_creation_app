import axios from "axios";
import type {
  GenerateDMRequest,
  GenerateDMResponse,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Error handling interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error);
    
    if (error.response) {
      // Server responded with error
      const detail = error.response.data?.detail || error.response.data?.message || `API Error: ${error.response.status}`;
      throw new Error(detail);
    } else if (error.request) {
      // Request made but no response
      console.error("No response received:", error.request);
      throw new Error(
        `ネットワークエラー: サーバーに接続できませんでした。\n` +
        `URL: ${API_BASE_URL}\n` +
        `サーバーが起動しているか確認してください。`
      );
    } else {
      // Something else happened
      console.error("Request setup error:", error.message);
      throw new Error(error.message || "予期しないエラーが発生しました");
    }
  }
);

export const dmApi = {
  /**
   * DM生成（通常版）
   */
  generateDM: async (request: GenerateDMRequest): Promise<GenerateDMResponse> => {
    const response = await apiClient.post<GenerateDMResponse>(
      "/api/dm/generate",
      request
    );
    return response.data;
  },

  /**
   * DM生成（ストリーミング版）
   * Server-Sent Eventsを使用して進捗を取得
   * Note: EventSourceはGETのみサポートのため、fetch + ReadableStreamを使用
   */
  generateDMStream: async (
    request: GenerateDMRequest,
    onProgress: (update: { stage: string; message: string; progress: number }) => void,
    onComplete: (result: GenerateDMResponse) => void,
    onError: (error: Error) => void
  ): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/dm/generate/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorText = await response.text().catch(() => "");
        throw new Error(
          `HTTP error! status: ${response.status}${errorText ? ` - ${errorText}` : ""}`
        );
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error("Response body is not readable");
      }

      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.stage === "completed" && data.result) {
                onComplete(data.result as GenerateDMResponse);
                return;
              } else if (data.error) {
                onError(new Error(data.error));
                return;
              } else {
                onProgress(data);
              }
            } catch (e) {
              console.error("Failed to parse SSE data:", e);
            }
          }
        }
      }
    } catch (error) {
      // より詳細なエラーメッセージを提供
      if (error instanceof TypeError && error.message.includes("Failed to fetch")) {
        onError(
          new Error(
            `バックエンドサーバーに接続できません。\n` +
            `サーバーが起動しているか確認してください: ${API_BASE_URL}\n` +
            `エラー: ${error.message}`
          )
        );
      } else {
        onError(error as Error);
      }
    }
  },
};

export default apiClient;
