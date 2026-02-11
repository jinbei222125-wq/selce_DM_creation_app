#!/bin/bash
# フロントエンドサーバー起動スクリプト

cd "$(dirname "$0")/frontend"

# node_modulesが存在しない場合はインストール
if [ ! -d "node_modules" ]; then
    echo "依存関係をインストール中..."
    npm install
fi

# サーバーを起動
echo "🚀 フロントエンドサーバーを起動中..."
echo "📍 http://localhost:3000"
npm run dev
