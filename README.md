# SoraCare v1.1

江東区・舞浜・表参道・渋谷・国分寺を切り替え、天気、時間別気圧、熱中症目安、冬季ヒートショック目安、約300字のAI総括を表示する、複数人利用向けの通知なしPWAです。

## ローカル起動

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

`http://127.0.0.1:5000` を開きます。OpenAI APIキーがなくても定型総括で動作します。

## Render

1. このフォルダをGitHubへアップロード
2. RenderでBlueprintまたはWeb Serviceを作成
3. AI総括を使う場合は `OPENAI_API_KEY` を登録

必要な環境変数：

```text
OPENAI_API_KEY=作成したAPIキー
OPENAI_MODEL=gpt-5-mini
```

## 複数人利用

ログイン・通知購読・個人データ保存はありません。同じURLを複数人で利用できます。端末ごとに最後に選んだ地域だけをブラウザ内へ保存します。

## 気圧データ

一般公開された頭痛ーる公式API仕様が確認できないため、Open-Meteoの時間別地上気圧を使用しています。正式な連携手段を利用できる場合は、`fetch_weather()` の取得部分を差し替えられます。

## 注意

熱中症・ヒートショック表示は生活上の目安であり、医療判断や公式警報の代替ではありません。
