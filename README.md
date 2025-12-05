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



# 🔮 Oracle Campus – 開発チーム向け README（初学者でも分かる完全ガイド）

ようこそ Oracle Campus の開発へ！  
この README は **初めての人でも迷わず開発に参加できること** を目的に書かれています。

---

# 📌 0. プロジェクト概要（簡単に）

Oracle Campus は、  
**「未来を予測して遊べる学内予測市場アプリ」** です。

- 予測をトークンでベット（賭け）し
- 結果が当たると報酬が増える  
- Streamlit + Python で動く簡単アプリ  
- データは JSON で管理（軽いWeb3擬似体験）

---

# 📌 1. 初回セットアップ（最初に一度だけ）

以下を順番にコピペしてください。

## 1-1. リポジトリを clone（ダウンロード）

```
cd 〇〇

git clone https://github.com/akatsukap/oracle-campus.git
cd oracle-campus

```


1-2. Python 仮想環境を作成

仮想環境とは？
プロジェクト専用の「Python の箱」。
他のプロジェクトの設定と混ざらないようにする安全装置！

python3 -m venv venv


作成されたか確認：

ls venv

1-3. 仮想環境を起動（※作業のたびに必要）
source venv/bin/activate


成功すると、ターミナルの先頭に (venv) と出ます。


1-4. 必要なライブラリをインストール

requirements.txt を使います。

pip install -r requirements.txt


入るもの：

streamlit

pandas

1-5. アプリが動くか確認（初回動作確認）
streamlit run app.py


ブラウザが開きます：

Local URL → http://localhost:8501

メールアドレスの入力画面は無視してOK → Enter を押す

画面が出れば成功です 🎉

📌 2. ブランチ運用ルール（重要）

開発は main ブランチを直接触らない！

🔵 main ブランチとは

常に“動く”状態

本番に最も近い状態

直接 push しない
→ Pull Request（PR）で変更する

🟢 feature/◯◯ ブランチとは

自分専用の作業ブランチです。

例：

feature/akatsukap

feature/add-vote-page

feature/admin-ui

📌 3. 自分の作業ブランチを作る（初回）
source venv/bin/activate

git checkout main
git pull origin main

git checkout -b feature/<自分の名前>
# 例：git checkout -b feature/yamada

📌 4. 毎日の作業前に必ず行うルーティン

全員が main の最新状態を取り込むための作業です。

source venv/bin/activate

git checkout main
git pull origin main

git checkout feature/<自分の名前>
git merge main


これであなたのブランチは最新状態になります。

---
##ブロックチェーンについて

作成したプログラムがブロックチェーン上に記述されているか確認するためにはEtherscanというツールを使用する
下記のURLに飛んでいける

https://sepolia.etherscan.io/address/0x3e54D97F57E940CB5836B1014969A50951083cF8#events

※ブロックチェーンのデプロイはミゾグチのウォレットからおこなっているので自身のPCでブロックチェーンに触れるのは記述されているのかの確認だけ
