#!/bin/bash
# バックエンドサーバー起動スクリプト

cd "$(dirname "$0")/backend"

# 仮想環境が存在しない場合は作成
if [ ! -d "venv" ]; then
    echo "仮想環境を作成中..."
    python3 -m venv venv
fi

# 仮想環境をアクティベート
source venv/bin/activate

# 依存関係をインストール（まだインストールされていない場合）
if ! python -c "import fastapi" 2>/dev/null; then
    echo "依存関係をインストール中..."
    pip install -r requirements.txt
fi

# .envファイルが存在しない場合は作成
if [ ! -f ".env" ]; then
    echo ".envファイルを作成中..."
    cp .env.example .env
    echo "⚠️  .envファイルにAPIキーを設定してください！"
fi

# データベーステーブルを作成
python -c "from app.db.base import Base, engine; Base.metadata.create_all(bind=engine)" 2>/dev/null

# サーバーを起動
echo "🚀 バックエンドサーバーを起動中..."
echo "📍 http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
uvicorn app.main:app --reload --port 8000
