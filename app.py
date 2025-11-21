import streamlit as st
from utils import load_data, save_data, init_sample_data

# ページ設定（タイトルなど）
st.set_page_config(
    page_title="Oracle Campus",
    page_icon="🎓",
    layout="wide",
)

st.title("Oracle Campus 🎓")
st.subheader("ユーザー選択（ログイン）")


# 1. データ読み込み ＋ なければ初期化
data = load_data()

if not data.get("users"):
    # 初回はサンプルデータで初期化
    data = init_sample_data()
    save_data(data)

users = list(data["users"].keys())

if not users:
    st.error("ユーザーデータが存在しません。utils.init_sample_data などで作成してください。")
    st.stop()

# 2. session_state に user_id を保持
if "user_id" not in st.session_state:
    st.session_state["user_id"] = users[0]

selected_user = st.selectbox(
    "ユーザーを選択してください：",
    users,
    index=users.index(st.session_state["user_id"]),
)

st.session_state["user_id"] = selected_user

st.markdown(f"現在ログイン中のユーザー： **{selected_user}**")

st.info("左のサイドバーから **Main / Vote / Results / Admin** ページに移動できます。")
