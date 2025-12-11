# Python 3.9-slim (軽量イメージ) をベースに使用
FROM python:3.9-slim

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係ファイルをコピー
COPY requirements.txt .

# 依存ライブラリをインストール
RUN pip install --no-cache-dir -r requirements.txt

# ソースコードをコピー
COPY . .

# Streamlitのデフォルトポート(8501)を公開
EXPOSE 8501

# ヘルスチェック (任意だが推奨)
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# アプリケーション起動コマンド
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
