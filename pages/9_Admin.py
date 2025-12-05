import os
import sys
# pages フォルダの親（プロジェクトルート）を path に追加して utils を import 可能にする
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import utils
from datetime import datetime, time

st.set_page_config(page_title="管理画面")

st.title("管理者パネル")

# Load data once at the start
data = utils.load_data()

# -------------------------
# ① マーケット作成 UI
# -------------------------
st.header("マーケット作成")

title = st.text_input("タイトル")
description = st.text_input("説明文（任意）")

# 日付（カレンダー）
end_date = st.date_input("締め切り日（カレンダーから選択）")

st.write("締め切り時刻（時・分を選択）")

col1, col2 = st.columns(2)

# --- 時をドロップダウンで選択 ---
with col1:
    hour = st.selectbox(
        "時（0〜23）",
        options=list(range(24)),
        index=12  # 初期選択＝12時
    )

# --- 分をドロップダウンで選択 ---
with col2:
    minute = st.selectbox(
        "分（0〜59）",
        options=list(range(60)),
        index=0
    )

# time オブジェクト作成
end_time = time(hour, minute)

# ISO形式 datetime
end_datetime = datetime.combine(end_date, end_time).isoformat()

if st.button("作成"):
    utils.create_market(data, title, description, end_datetime)
    utils.save_data(data)
    st.success("マーケットを作成しました！🌟")


st.markdown("---")


# -------------------------
# ② 結果確定 UI
# -------------------------
st.header("結果確定パネル")

markets = utils.list_markets(data)
now = datetime.now()

targets = []
for m in markets:
    if m.get("status") == "open":
        end_dt_str = m.get("end_datetime")
        if end_dt_str:
            try:
                if datetime.fromisoformat(end_dt_str) < now:
                    targets.append(m)
            except (ValueError, TypeError):
                pass

if not targets:
    st.info("確定可能なマーケットはありません。")
else:
    for m in targets:
        st.subheader(m["title"])
        st.write(m.get("description", ""))

        result = st.radio("結果", ["Yes", "No"], key=f"r_{m['id']}")

        if st.button("結果を確定する", key=f"b_{m['id']}"):
            utils.resolve_market(data, m["id"], result)
            utils.save_data(data)
            st.success(f"{m['title']} の結果を {result} に確定しました！")
            st.rerun()
