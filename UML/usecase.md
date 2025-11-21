```mermaid
usecaseDiagram
    actor Student as "学生(User)"
    actor Admin as "管理者(Admin)"
    
    package OracleCampus {
        usecase "トークンをもらう(Faucet)" as UC1
        usecase "予測市場一覧を見る" as UC2
        usecase "予測にベットする" as UC3
        usecase "配当を引き出す" as UC4
        usecase "ランキングを見る" as UC5
        usecase "市場を作成する" as UC6
        usecase "結果を確定する" as UC7
    }
    
    Student --> UC1
    Student --> UC2
    Student --> UC3
    Student --> UC4
    Student --> UC5
    
    Admin --> UC6

    Admin --> UC7
```
