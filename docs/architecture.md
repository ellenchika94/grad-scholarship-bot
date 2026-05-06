# アーキテクチャ概要

## 全体像

```
[GitHub Actions cron] --(隔週月曜9:00 JST)--> [bot/main.py]
                                                  |
                              ┌───────────────────┼───────────────────┐
                              ▼                   ▼                   ▼
                        [scrapers/*]         [db (SQLite)]    [discord_post]
                              │                   │                   │
                       RSS/HTML取得         新着判定/締切管理      Webhook送信
```

## ディレクトリ構成

```
grad-scholarship-bot/
├── bot/
│   ├── config.py           # 環境変数・定数
│   ├── db.py               # SQLite I/O
│   ├── discord_post.py     # Webhook投稿
│   ├── main.py             # オーケストレータ
│   └── scrapers/
│       ├── base.py         # Scraper基底クラス、ScholarshipItem
│       ├── washimaru.py    # わしまる大学（国内）
│       └── xplane.py       # XPLANE（海外）
├── data/
│   └── scholarships.db     # SQLite（リポジトリにcommitして永続化）
├── .github/workflows/
│   └── biweekly.yml        # 隔週cron
└── requirements.txt
```

## DBスキーマ

```sql
scholarships(
  id, source, external_id, title, url, deadline,
  region ('domestic'|'overseas'),
  first_seen_at, notified_new, reminder_7_sent, reminder_3_sent,
  UNIQUE(source, external_id)
)
```

差分管理は `(source, external_id)` のUNIQUE制約で実現。
新規挿入時のみ新着扱い。

## 新しいスクレイパーの追加方法

1. `bot/scrapers/{source_id}.py` を作成
2. `Scraper` を継承し以下を定義：
   - `source_id` (str): DB保存用ユニークID
   - `source_label` (str): Discord表示用ラベル
   - `region` ('domestic'|'overseas')
   - `fetch()` -> `Iterable[ScholarshipItem]`
3. `bot/scrapers/__init__.py` の `ALL_SCRAPERS` に追加

### 例：RSSベース

```python
from .base import Scraper, ScholarshipItem

class MySite(Scraper):
    source_id = "mysite"
    source_label = "サイト名"
    region = "domestic"
    feed_url = "https://example.com/feed/"

    def fetch(self):
        feed = self.parse_feed(self.feed_url)
        for entry in feed.entries:
            yield ScholarshipItem(
                external_id=entry.get("id") or entry.link,
                title=entry.title,
                url=entry.link,
                deadline=None,
                region=self.region,
            )
```

### 例：HTMLスクレイピング

```python
from bs4 import BeautifulSoup
from .base import Scraper, ScholarshipItem

class MySite(Scraper):
    source_id = "mysite"
    ...

    def fetch(self):
        resp = self.get("https://example.com/list")
        soup = BeautifulSoup(resp.text, "lxml")
        for card in soup.select(".scholarship-card"):
            yield ScholarshipItem(...)
```

`self.get()` はレート制限（10秒）と User-Agent を自動付与する。

## 実行とデバッグ

```bash
# ローカル動作確認（Webhook空でも動く）
DISCORD_WEBHOOK_DOMESTIC="" DISCORD_WEBHOOK_OVERSEAS="" python -m bot.main

# DB確認
sqlite3 data/scholarships.db "SELECT source, COUNT(*) FROM scholarships GROUP BY source"
```

## GitHub Actions の cron 仕様

GitHub Actions の cron は「隔週」を直接指定できない。回避策として：
- 毎週月曜0:00 UTC（9:00 JST）に発火
- ワークフロー内で「今日が1〜7日 or 15〜21日の月曜」かをチェック
- それ以外はスキップ

`workflow_dispatch` で手動実行も可能（テスト用）。

## Discord Webhook の Secrets

GitHub リポジトリの Settings → Secrets and variables → Actions に：
- `DISCORD_WEBHOOK_DOMESTIC`: 国内チャンネル用Webhook URL
- `DISCORD_WEBHOOK_OVERSEAS`: 海外チャンネル用Webhook URL
- `CONTACT_EMAIL`: スクレイピング先への連絡先メアド（User-Agentに含める）

## 倫理・運用ポリシー

- 本文の転載をしない（タイトル・締切・公式URLのみ）
- 各投稿に出典を明記
- アクセス間隔は10秒（`config.REQUEST_INTERVAL_SEC`）
- 巡回は隔週1回
- User-Agent に連絡先メアド明記
- robots.txt 尊重
- 規約で明示的に自動収集禁止のサイトは対象外
