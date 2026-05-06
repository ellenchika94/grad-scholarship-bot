# grad-scholarship-bot

大学院進学コミュニティ向け、奨学金情報をDiscordへ自動配信するBot。

## 動作概要

- 2週間に1回、奨学金アグリゲータサイトを巡回
- 新着募集を検出してDiscordチャンネルに投稿（国内 / 海外で振り分け）
- 締切が近い募集（7日前・3日前）をリマインダ投稿

## 情報源

### 国内（修士向け）
- [JASSO 大学院奨学金検索](https://www.jasso.go.jp/shogakukin/jrec/index.html)
- [ガクシー](https://gaxi.jp/)
- [わしまる大学](https://washimaru-univ.com/)

### 海外大学院向け
- [JASSO 海外留学奨学金検索](https://ryugaku.jasso.go.jp/scholarship/)
- [XPLANE Scholarship Database](https://xplane.jp/fellowships-list/)

## 倫理ポリシー

- 本文転載しない（タイトル・締切・公式URLのみ）
- 各投稿に必ず出典を明記
- アクセス間隔10秒以上、巡回は隔週1回のみ
- User-Agent に連絡先を明示
- robots.txt 尊重

## 実行

GitHub Actions により自動実行。手動実行は `Actions` タブから `Run workflow`。

## ローカル開発

```bash
pip install -r requirements.txt
cp .env.example .env  # Webhook URL を記入
python -m bot.main
```
