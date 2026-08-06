# SoraCare v1.3 Instant

通知なし・複数人利用向けの高速表示版です。

## 改善点
- PWA画面をキャッシュから即表示（Renderがスリープ中でも2回目以降は画面が開きやすい）
- 前回取得した天気を端末内に保存し、起動直後に表示
- 最新のOpen-Meteoデータはバックグラウンド更新
- AI総括は天気表示後に別取得
- API待ちに上限時間を設定

## Render
Root Directory: `SoraCare_v1.3_instant`（リポジトリ直下の配置に応じて変更）
Build Command: `pip install -r requirements.txt`
Start Command: `gunicorn app:app --timeout 120`

## 環境変数
OPENAI_API_KEY=あなたのAPIキー
OPENAI_MODEL=gpt-5-mini

初回アクセスだけはRender無料枠のコールドスタートが発生する可能性があります。2回目以降はPWAキャッシュと端末保存データを先に表示します。
