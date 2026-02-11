#!/bin/bash
# 依存関係インストールスクリプト（Rust不要版）

cd "$(dirname "$0")"

echo "📦 依存関係をインストール中..."

# 仮想環境をアクティベート
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ 仮想環境が見つかりません。先に python3 -m venv venv を実行してください。"
    exit 1
fi

# まず、tiktokenを事前ビルド済みwheelでインストール（Rust不要）
echo "🔧 tiktokenを事前ビルド済みwheelでインストール..."
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --only-binary=:all: tiktoken 2>/dev/null || \
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --only-binary=tiktoken "tiktoken>=0.5.1,<0.6.0"

# 残りの依存関係をインストール
echo "📚 その他の依存関係をインストール..."
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

echo "✅ インストール完了！"
