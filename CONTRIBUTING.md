# 開発・コントリビュート

## 環境構築

```bash
git clone https://github.com/<owner>/grad-scholarship-bot.git
cd grad-scholarship-bot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env  # Webhook URL等を設定
```

## ローカル実行

```bash
# Webhook URL なしでも動作確認できる（投稿だけスキップ）
DISCORD_WEBHOOK_DOMESTIC="" DISCORD_WEBHOOK_OVERSEAS="" python -m bot.main
```

## 新しい奨学金ソースを追加するには

詳細は [docs/architecture.md](docs/architecture.md) を参照。

## PRフロー

1. issueを立てて何をするか共有
2. ブランチ切ってPR
3. ローカルで `python -m bot.main` が通ることを確認
4. レビュー → マージ

## 追加して良いソース／だめなソース

**OK**
- 公的機関の公式情報（JASSO等）
- アグリゲータサイトでスクレイピング・自動収集を**規約で明示禁止していない**もの
- RSSフィードを公開しているサイト

**NG**
- 利用規約で「スクレイピング禁止」「自動収集禁止」を明記しているサイト
- robots.txt の Disallow 対象パス
- 個人運営の小規模ブログ等で、運営者が嫌がる可能性が高いもの（事前打診を推奨）

## 倫理ポリシー

詳細は README と docs/architecture.md。要点：
- 本文転載しない（タイトル・締切・URLのみ）
- 出典明記
- アクセス間隔10秒以上、巡回は隔週1回
- User-Agent に連絡先メアド
