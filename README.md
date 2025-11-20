# Oracle Campus 🎓

**Oracle Campus** は、大学内の「未来」をみんなで予測して楽しむ  
**予測市場（Prediction Market）風アプリ** です。

今回は、本物のブロックチェーンではなく

- Python
- Streamlit
- JSONファイル（`data/database.json`）

を使って、**「疑似ブロックチェーン」版**として開発しています。

将来的には、このロジックをスマートコントラクトに置き換えることで、  
本物の Web3 アプリへ拡張できる構成を目指しています。

---

## 🧩 なにができるアプリ？

- 「明日の天気は晴れる？」「学祭は来場者〇〇人を超える？」などのイベントを作成
- 学生は、配布されたポイント（OCP: Oracle Campus Point）を
  - **Yes / No** どちらかにベット（投票）
- 結果が当たるとポイントが増え、外れると減る
- 「誰が一番、未来を見通す目を持っているか？」をランキングで可視化

---

## 🛠 技術スタック

- 言語: Python 3.8+
- フレームワーク: Streamlit
- データ保存: JSON ファイル（`data/database.json`）
- 実行環境: WSL2 + Ubuntu（推奨）
- バージョン管理: Git / GitHub

---

## 📁 ディレクトリ構成

```text
oracle-campus/
├── app.py            # アプリの入口（ページ遷移・ユーザー選択など）
├── utils.py          # データ読み書き・投票ロジック（疑似ブロックチェーン）
├── data/
│   └── database.json # ユーザー・マーケット・ベット情報が入るJSON
├── pages/
│   ├── 1_Main.py     # メイン画面（イベント一覧・残高表示など）
│   ├── 2_Vote.py     # 投票画面（Yes/No にポイントを賭ける）
│   ├── 3_Results.py  # 結果・ランキング画面
│   └── 9_Admin.py    # 管理画面（イベント作成・結果確定）
├── requirements.txt  # Python 依存ライブラリ（streamlit, pandas など）
└── venv/             # 仮想環境（Gitでは無視する）
# oracle-campus
大学向け予測市場アプリ（Streamlit）
