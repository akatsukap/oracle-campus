# import os
# import sys
# # pages フォルダの親（プロジェクトルート）を path に追加して utils を import 可能にする
# sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# import streamlit as st
# from utils.web3_manager.py import utils
# from datetime import datetime, time

# パスを通す


# st.set_page_config(page_title="管理画面")

# st.title("管理者パネル")

# # -------------------------
# # ① マーケット作成 UI
# # -------------------------
# st.header("マーケット作成")

# title = st.text_input("タイトル")
# description = st.text_input("説明文（任意）")

# # 日付（カレンダー）
# end_date = st.date_input("締め切り日（カレンダーから選択）")

# st.write("締め切り時刻（時・分を選択）")

# col1, col2 = st.columns(2)

# # --- 時をドロップダウンで選択 ---
# with col1:
#     hour = st.selectbox(
#         "時（0〜23）",
#         options=list(range(24)),
#         index=12  # 初期選択＝12時
#     )

# # --- 分をドロップダウンで選択 ---
# with col2:
#     minute = st.selectbox(
#         "分（0〜59）",
#         options=list(range(60)),
#         index=0
#     )

# # time オブジェクト作成
# end_time = time(hour, minute)

# # ISO形式 datetime
# end_datetime = datetime.combine(end_date, end_time).isoformat()

# if st.button("作成"):
#     utils.create_market(title, description, end_datetime)
#     st.success("マーケットを作成しました！🌟")


# st.markdown("---")


# # -------------------------
# # ② 結果確定 UI
# # -------------------------
# st.header("結果確定パネル")

# markets = utils.list_markets()
# now = datetime.now()

# targets = [
#     m for m in markets
#     if m["status"] == "open" and datetime.fromisoformat(m["end_datetime"]) < now
# ]

# if not targets:
#     st.info("確定可能なマーケットはありません。")
# else:
#     for m in targets:
#         st.subheader(m["title"])
#         st.write(m["description"])

#         result = st.radio("結果", ["Yes", "No"], key=f"r_{m['id']}")

#         if st.button("結果を確定する", key=f"b_{m['id']}"):
#             utils.resolve_market(m["id"], result)
#             st.success(f"{m['title']} の結果を {result} に確定しました！")
#             st.rerun()

import streamlit as st
from datetime import datetime, time
import sys
import os
import style_config as sc

#デザイン統一
sc.apply_common_style()


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------
# 🔒 ① ここにアクセス制限を追加！
# ---------------------------------------------
st.set_page_config(page_title="管理者画面", layout="wide", page_icon="🛡️")

# セッションから現在のユーザーIDを取得
user_id = st.session_state.get("user_id")

# admin以外なら追い出す
if user_id != "admin":
    st.error("⛔️ アクセス権限がありません！")
    st.warning("このページは管理者専用です。サイドバーから他のページに移動してください。")
    st.stop()  # ←これで処理を強制終了させる
from utils.web3_manager import Web3Manager
# 1. Web3接続チェック
try:
    manager = Web3Manager()
    st.success("Web3 接続成功 ✅")
except Exception as e:
    st.error(f"Web3接続エラー: {e}")
    st.warning("⚠️ .envファイルの設定を確認してください。")
    st.stop()

# タブで機能を分ける
tab1, tab2 = st.tabs(["📝 マーケット作成", "⚖️ 結果確定 (Oracle)"])

# -------------------------
# ① マーケット作成 UI
# -------------------------
with tab1:
    st.header("新規予測イベントの発行")

    title = st.text_input("イベント名", placeholder="例: 明日のサークル対抗戦はAチームが勝つ？")
    # ※descriptionはブロックチェーンの容量節約のため今回は省略します
    
    st.write("---")
    st.subheader("締め切り設定")
    
    col1, col2 = st.columns(2)
    with col1:
        end_date = st.date_input("日付")
    with col2:
        end_time_val = st.time_input("時刻", value=time(12, 0))

    if st.button("🚀 ブロックチェーンに発行する"):
        if not title:
            st.warning("タイトルを入力してください。")
        else:
            # 【重要】スマートコントラクト用に「残り秒数」を計算する
            deadline_dt = datetime.combine(end_date, end_time_val)
            now_dt = datetime.now()
            
            # 締め切りまでの秒数
            duration_sec = (deadline_dt - now_dt).total_seconds()
            
            if duration_sec <= 0:
                st.error("⚠️ 締め切りは「未来の日時」に設定してください！")
            else:
                with st.spinner("ブロックチェーンに書き込み中... (署名して送信)"):
                    try:
                        # 整数に変換して渡す
                        tx_receipt = manager.create_market(title, int(duration_sec))
                        
                        st.success("マーケット作成成功！ブロックチェーンに刻まれました。")
                        st.write(f"Tx Hash: `{tx_receipt['transactionHash'].hex()}`")
                        st.balloons()
                    except Exception as e:
                        st.error(f"作成失敗: {e}")

# -------------------------
# ② 結果確定 UI
# -------------------------
with tab2:
    st.header("結果の確定 (Oracle機能)")
    st.caption("イベントが終了したら、ここで正解を入力して配当を分配可能にします。")
    
    # Web3から最新データを取得
    try:
        markets = manager.get_all_markets()
    except Exception as e:
        st.error("データ取得失敗")
        st.stop()
    
    # まだ解決していない(resolved=False)市場だけ抽出
    active_markets = [m for m in markets if not m['resolved']]
    
    if not active_markets:
        st.info("現在、結果待ちのイベントはありません。")
    else:
        # ドロップダウンで選ばせる
        selected_market_id = st.selectbox(
            "結果を確定するイベントを選択",
            options=[m['id'] for m in active_markets],
            format_func=lambda x: f"ID:{x} {next((m['title'] for m in active_markets if m['id']==x), '')}"
        )
        
        # 選ばれた市場の情報を表示
        target = next((m for m in active_markets if m['id'] == selected_market_id), None)
        
        if target:
            st.info(f"イベント: **{target['title']}**")
            
            # 締め切り日時の表示
            deadline = datetime.fromtimestamp(target['endTime'])
            st.write(f"締め切り日時: **{deadline.strftime('%Y/%m/%d %H:%M')}**")
            
            # 締め切り前のアラート
            if datetime.now() < deadline:
                st.warning("⚠️ 注意: まだ締め切り時刻を過ぎていません。今確定すると早期終了になります。")
            
            st.write("---")
            st.write("##### 正解はどっちでしたか？")
            col_yes, col_no = st.columns(2)
            
            if col_yes.button("⭕️ YES (正解)"):
                with st.spinner("結果をブロックチェーンに記録中..."):
                    manager.resolve_market(target['id'], True)
                    st.success("結果を YES で確定しました！配当分配の準備完了です。")
                    
            if col_no.button("❌ NO (不正解)"):
                with st.spinner("結果をブロックチェーンに記録中..."):
                    manager.resolve_market(target['id'], False)
                    st.success("結果を NO で確定しました！配当分配の準備完了です。")
