stateDiagram-v2
    [*] --> Open : 市場作成(Admin)
    Open --> Open : ベット受付中
    Open --> Closed : 締め切り時刻到来
    Closed --> Resolved : 結果入力(Admin)
    Resolved --> Resolved : 配当受取可能(User)
    Resolved --> [*]