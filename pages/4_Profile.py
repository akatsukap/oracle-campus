import streamlit as st
import pandas as pd
try:
    from utils.web3_manager import Web3Manager
except ImportError:
    st.error("utils/web3_manager.py が見つかりません")
    st.stop()

def app():
    st.set_page_config(page_title="マイプロフィール", page_icon="👤")
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("まずトップページでユーザーを選択してください。")
        st.stop()
    
    display_name = user_id
    st.title(f"👤{display_name}さんのプロフィール&実績")
    try:
        manager = Web3Manager()
    except Exception as e:
        st.error("Web3接続エラー")
        st.stop()


    # 1. ユーザー情報の取得（今回はデモ用に開発者のアドレス＝自分と仮定）
    # 本来はログイン中のユーザーアドレスを使う
    my_address = manager.account.address
    st.write(f"Wallet Address: `{my_address}`")

    # 残高表示
    balance = manager.get_my_balance()
    st.metric("現在の資産", f"{balance} OCP")

    st.divider()

    # 2. 的中率の計算（Pythonで頑張るパート）
    st.subheader("📊 予言の戦績")

    # 全市場データを取得
    all_markets = manager.get_all_markets()

    # 集計用変数
    total_bets = 0
    wins = 0

    # ※注意: ここは簡易ロジックです。
    # 本当は「自分が賭けた履歴」を保存しておくべきですが、
    # 今回は「結果が出た市場」をループして「もし賞金を請求済みなら勝ち」とみなす等の工夫が必要です。
    # 5週間開発用の「簡略化ロジック」として、ここではデモ用に数字をシミュレーションします。
    # ★プレゼン本番では、手動で変数をいじって「80%超え」を見せるとスムーズです！

    # --- デモ用ダミーロジック (プレゼンで動かす用) ---
    # 実際はここでデータベース等から履歴を引く
    total_bets = 10  # 仮: 10回参加
    wins = 8         # 仮: 8回的中
    # -------------------------------------------

    accuracy = (wins / total_bets) * 100 if total_bets > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("参加回数", f"{total_bets} 回")
    col2.metric("的中回数", f"{wins} 回")
    col3.metric("的中率", f"{accuracy:.1f} %")

    st.divider()

    # 3. SBTバッジのセクション
    st.subheader("🏆 予言者バッジ (SBT)")

    # すでに持っているかチェック
    has_badge = manager.has_sbt(my_address)

    if has_badge:
        st.success("🎉 あなたは公認の予言者です！")
        st.image("https://img.icons8.com/color/480/medal.png", width=200, caption="Oracle Prophet Badge")
        st.caption("このバッジはブロックチェーンに刻まれ、他人に譲渡することはできません。")

    else:
        if accuracy >= 80 and total_bets >= 5:
            st.info("🔥 おめでとうございます！的中率が80%を超えました。")
            st.write("予言者の称号（SBT）を獲得できます。")
            
            if st.button("SBTを受け取る (Mint)"):
                with st.spinner("ブロックチェーンに称号を刻んでいます..."):
                    manager.mint_sbt(my_address)
                    st.balloons()
                    st.success("獲得しました！リロードしてください。")
        else:
            st.warning("🔒 バッジ獲得条件: 5回以上参加し、的中率80%以上")
            st.write(f"あと {5 - total_bets} 回の参加が必要です。")
if __name__ == "__main__":
    app()