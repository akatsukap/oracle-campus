import streamlit as st
import time
from datetime import datetime

# 作成した Web3Manager を読み込む
# ※ 環境に合わせて data.fibase からインポートするように調整
try:
    from data.fibase import Web3Manager
except ImportError:
    st.error("data/fibase.py が見つかりません。配置を確認してください。")
    st.stop()

def app():
    # ページ設定（ページ単体で実行された場合の設定）
    try:
        st.set_page_config(page_title="Oracle Campus", page_icon="🎓")
    except:
        pass

    st.title("Oracle Campus 🎓")
    st.subheader("予測市場ダッシュボード")

    # ─────────────────────────────
    # 1. Web3 接続 & データ取得
    # ─────────────────────────────
    try:
        # Web3マネージャーを起動
        manager = Web3Manager()
        
        # 自分の残高を表示
        my_balance = manager.get_balance()
        st.sidebar.metric(label="あなたの所持ポイント", value=f"{my_balance} OCP")
        
        # 全市場データをブロックチェーンから取得
        markets = manager.get_all_markets()
        
    except Exception as e:
        st.error(f"Web3接続エラー: {e}")
        st.warning("⚠️ .envファイルの設定や、RPC URLが正しいか確認してください。")
        st.stop()

    st.divider()

    # ─────────────────────────────
    # 2. 募集中のイベント一覧を表示
    # ─────────────────────────────
    st.markdown("### 📈 募集中の予測イベント")

    # まだ結果が出ていない（resolved == False）市場だけを抽出
    open_markets = [m for m in markets if not m['resolved']]
    
    # 締め切りが近い順に並び替え
    open_markets.sort(key=lambda x: x['endTime'])

    if not open_markets:
        st.info("現在、投票受付中のイベントはありません。管理者画面から作成してください。")
    else:
        for m in open_markets:
            # コンテナを使ってカード風に表示
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"#### 🟢 {m['title']}")
                    
                    # 締め切り日時の表示変換
                    end_ts = int(m['endTime'])
                    end_date = datetime.fromtimestamp(end_ts)
                    
                    # 現在時刻と比較して終了済みかチェック
                    is_ended = end_ts < time.time()
                    status_text = "終了" if is_ended else "受付中"
                    st.caption(f"状態: {status_text} | 締切: {end_date.strftime('%Y/%m/%d %H:%M')}")
                    
                    # 投票状況の可視化
                    total_pool = m['totalYes'] + m['totalNo']
                    if total_pool > 0:
                        yes_ratio = m['totalYes'] / total_pool
                        st.progress(yes_ratio, text=f"Yes率: {int(yes_ratio*100)}%")
                    else:
                        st.text("まだ投票がありません")

                with col2:
                    st.write(f"Yes: **{m['totalYes']}**")
                    st.write(f"No: **{m['totalNo']}**")
                    
                    # 「投票する」ボタン
                    if not is_ended:
                        if st.button("投票へ進む 🗳️", key=f"btn_{m['id']}"):
                            st.session_state["selected_market_id"] = m['id']
                            st.success(f"「{m['title']}」を選択しました！\nサイドバーから「Vote」ページに移動してください。")
                    else:
                        # ここがエラーの原因でした。正しく修正しました。
                        st.button("受付終了", disabled=True, key=f"btn_end_{m['id']}")

            st.divider()

if __name__ == "__main__":
    app()