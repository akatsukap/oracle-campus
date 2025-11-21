import streamlit as st
import utils

# ユーザー一覧の取得
data = utils.load_data()
users = data.get("users", {})

# ユーザーIDの選択
if not users:
    st.error("ユーザー情報がありません。")
    st.stop()

user_id = st.selectbox(
    "ユーザーを選んでください",
    options=list(users.keys()),
    format_func=lambda uid: users[uid].get("name", uid)
)
# セッションに保存
st.session_state["user_id"] = user_id

# 1. ログイン中ユーザーIDの取得
user_id = st.session_state.get("user_id")

if not user_id:
    st.warning("先にユーザーを選んでください")
    st.stop()

# 2. マーケット一覧の取得・オープンのみ選択肢に
markets = data.get("markets", {})
open_markets = {mid for mid in markets if mid["status"] == "open"}

if not open_markets:
    st.info("現在投票可能なマーケットはありません。")
    st.stop()

market_id = st.selectbox(
    "マーケットを選択してください",
    options=list(open_markets.keys()),
    format_func=lambda mid: open_markets[mid].get("title", f"マーケットID: {mid}")
)

# 3. Yes / No の選択
side = st.radio("どちらに賭けますか？", ("yes", "no"))

# 4. ユーザー残高確認
user = users.get(user_id)
if not user:
    st.error("ユーザー情報が見つかりません")
    st.stop()
balance = user.get("balance", 0)

# 5. ベットポイント入力
amount = st.number_input("賭けるポイント数を入力してください（OCP）", min_value=1, max_value=balance, step=1)

# 6. 投票ボタン
if st.button("投票する"):
    try:
        message = utils.vote(user_id, market_id, side, amount)
        st.success(message)
    except Exception as e:
        st.error(str(e))