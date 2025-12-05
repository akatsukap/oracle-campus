import streamlit as st
import pandas as pd
import utils


def main():
	st.title("結果・ランキング")

	# Load actual data from the database
	data = utils.load_data()
	users = data.get("users", {})
	bets = data.get("bets", [])
	
	# Calculate scores based on user points
	# Higher points = better ranking (shows prediction accuracy)
	participants = []
	for user_id, user_data in users.items():
		points = user_data.get("points", 0)
		participants.append({"name": user_id, "score": points})
	
	if not participants:
		st.info("まだ参加者がいません。")
		return
	
	df = pd.DataFrame(participants)
	# 降順でソートして順位を付与
	df = df.sort_values(by="score", ascending=False).reset_index(drop=True)
	df["rank"] = df.index + 1

	# Get current user from session
	current_user = st.session_state.get("user_id")
	
	# 自分の行を取得
	me_row = df[df["name"] == current_user] if current_user else pd.DataFrame()
	if not me_row.empty:
		my_score = int(me_row.iloc[0]["score"])
		my_rank = int(me_row.iloc[0]["rank"])
	else:
		my_score = 0
		my_rank = "-"

	cols = st.columns([1, 2])
	cols[0].metric(label="あなたのスコア", value=f"{my_score} OCP")
	cols[1].metric(label="あなたの順位", value=f"{my_rank} / {len(df)}")

	st.markdown("---")
	st.subheader("全参加者のランキング")

	# テーブル表示：順位・名前・スコア
	display_df = df[["rank", "name", "score"]].copy()
	display_df = display_df.rename(columns={"rank": "順位", "name": "名前", "score": "スコア (OCP)"})

	# 表を出す（自分の行にマークをつける）
	def format_row(row):
		if current_user and row["名前"] == current_user:
			return f"**{row['名前']} (あなた)**"
		return row["名前"]

	# Streamlit では DataFrame の一部書式が限定されるので、表示用に変換してから書く
	disp = display_df.copy()
	disp["名前"] = disp.apply(format_row, axis=1)

	st.table(disp)


if __name__ == "__main__":
	main()

