# Insight DM Master

AI-powered personalized sales DM generation tool built with Next.js, FastAPI, and LangChain.

## 🚀 Technology Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui, TanStack Query
- **Backend**: Python (FastAPI), LangChain, LangGraph, Pydantic v2
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **AI**: GPT-4o (OpenAI), Tavily API (Web Search)

## 📁 Project Structure

```
/
├── frontend/
│   ├── src/
│   │   ├── app/                    # Next.js App Router
│   │   ├── components/
│   │   │   ├── ui/                 # shadcn/ui shared components
│   │   │   └── features/           # Business logic components
│   │   │       └── dm-generator/   # DM feature components
│   │   ├── services/               # API client
│   │   ├── hooks/                  # React hooks
│   │   └── types/                  # TypeScript types
│   └── public/
├── backend/
│   ├── app/
│   │   ├── api/                    # API endpoints/routers
│   │   ├── core/                   # Config, Security
│   │   ├── services/               # Business logic
│   │   │   └── ai/                 # LangGraph/LangChain agents
│   │   ├── schemas/                # Pydantic models
│   │   ├── models/                 # SQLAlchemy models
│   │   └── db/                     # Database session
│   ├── main.py
│   └── requirements.txt
└── docker-compose.yml
```

## 🛠️ セットアップ

### 前提条件

- Python 3.11+
- Node.js 18+
- OpenAI API Key
- Tavily API Key

### バックエンドのセットアップ

```bash
cd backend

# 仮想環境を作成
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt

# 環境変数を設定
cp .env.example .env
# .envファイルを編集してAPIキーを設定
# OPENAI_API_KEY=your_key_here
# TAVILY_API_KEY=your_key_here

# データベーステーブルを作成
python -c "from app.db.base import Base, engine; Base.metadata.create_all(bind=engine)"

# サーバーを起動
uvicorn app.main:app --reload --port 8000
```

または、起動スクリプトを使用：

```bash
./start-backend.sh
```

### フロントエンドのセットアップ

```bash
cd frontend

# 依存関係をインストール（初回のみ）
npm install

# 開発サーバーを起動
npm run dev
```

または、起動スクリプトを使用：

```bash
./start-frontend.sh
```

### アクセス

- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://localhost:8000
- **API ドキュメント**: http://localhost:8000/docs

## 🔑 APIキーの取得

### OpenAI API Key
1. [OpenAI Platform](https://platform.openai.com/) にアクセス
2. API Keys セクションで新しいキーを作成

### Tavily API Key
1. [Tavily](https://tavily.com/) にアクセス
2. アカウントを作成してAPIキーを取得

## 📖 使い方

1. **フォームに入力**:
   - 相手のURL（必須）
   - ターゲット情報（役職、会社名など、任意）
   - あなたの商材情報（商材名、要約、必須）

2. **「AI で DM を生成」をクリック**:
   - AIパイプラインが自動的に：
     - **調査**: 企業の最新ニュースや動向を検索
     - **分析**: 3つの魅力的なフックを抽出
     - **執筆**: 3つのトーンでDM案を生成

3. **結果を確認**:
   - 左側: Evidence（証拠）とHooks（話題）- クリックで選択可能
   - 右側: 生成されたDM案 - 編集・コピー可能

## 🎨 Features

- **Real-time Progress**: See research → analyze → write stages
- **Interactive Hooks**: Toggle hooks to customize generation
- **Editable Drafts**: Edit generated DMs inline
- **Markdown Support**: Rich formatting in DM drafts
- **Source Links**: View original evidence URLs
- **Multiple Tones**: Polite, Casual, Problem-solver

## 🔄 AI Pipeline

```
User Input
    ↓
[Researcher Agent] → Tavily Web Search
    ↓
[Analyzer Agent] → Extract 3 Hooks
    ↓
[Copywriter Agent] → Generate 3 DM Drafts
    ↓
Display Results
```

## 🔧 トラブルシューティング

### 「Failed to fetch」エラーが発生する場合

1. **バックエンドサーバーが起動しているか確認**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **バックエンドサーバーを起動**:
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn app.main:app --reload --port 8000
   ```

3. **ポートが使用されている場合**:
   ```bash
   lsof -i :8000  # バックエンド
   lsof -i :3000  # フロントエンド
   ```

### SSL証明書エラーが発生する場合

```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### tiktokenビルドエラーが発生する場合

```bash
# 事前ビルド済みwheelを使用
pip install --only-binary=:all: tiktoken
pip install -r requirements.txt
```

## 📝 License

MIT License
