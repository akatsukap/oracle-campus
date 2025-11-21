sequenceDiagram
    participant Student as 学生
    participant UI as Streamlit画面
    participant Contract as スマートコントラクト
    participant Chain as ブロックチェーン

    Student->>UI: 「Yes」に10 OCPベット
    UI->>Contract: bet(marketId, true, 10)を呼び出し
    Contract-->>Student: MetaMask署名リクエスト
    Student->>Contract: 署名(承認)
    Contract->>Chain: トランザクション送信
    Chain-->>Contract: 承認完了(Block生成)
    Contract-->>UI: 完了通知
    UI-->>Student: 「ベット完了しました！」表示
    UI->>Chain: 最新のオッズ情報を再取得
    Chain-->>UI: データ返却
    UI-->>Student: 画面更新(賭け金増加を確認)