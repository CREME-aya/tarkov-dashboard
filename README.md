# Tarkov Tactical Dashboard

Escape from Tarkov (EfT) のアイテム検索、タスク情報、弾薬性能などを一元管理できるStreamlitアプリケーションです。
Tarkov.dev APIを使用しており、常に最新のマーケット価格やトレーダー情報を取得できます。

## 主な機能
- **アイテム相場検索**: フリマ価格、トレーダー買取/販売価格、購入条件（LL, タスク）を一括表示。
- **タスク必要品リスト**: アイテムが「どのトレーダーの」「どのタスクで」必要かを一覧化。
- **バーター(交換)検索**: アイテムの「交換入手レシピ」と「素材としての使い道」を検索。
- **弾薬性能チャート**: 弾薬の貫通力とダメージを可視化。
- **クラフト利益計算**: 隠れ家(Hideout)での生産利益を計算。
- **多言語対応**: 日本語 / 英語 切り替え可能。

## 動作環境
- Python 3.9+
- Streamlit
- Pandas
- Requests

## インストールと実行
### ローカルで実行する場合
```bash
# 依存ライブラリのインストール
pip install -r requirements.txt

# アプリの起動
streamlit run app.py
```

### Dockerで実行する場合
```bash
# ビルド
docker build -t tarkov-dashboard .

# 実行
docker run -p 8501:8501 tarkov-dashboard
```

## デプロイ方法 (Streamlit Community Cloud)
1. このリポジトリをGitHubにプッシュします。
2. [Streamlit Community Cloud](https://streamlit.io/cloud) にログインします。
3. "New app" をクリックし、このリポジトリを選択します。
4. "Deploy!" をクリックすると、WEB上で誰でもアクセス可能になります。

## クレジット
- API: [Tarkov.dev](https://tarkov.dev/)
