import streamlit as st
import pandas as pd


def main():
	st.title("結果・ランキング")

	# サンプルデータ（実際はデータベースや JSON から読み込む想定）
	participants = [
		{"name": "Aさん", "score": 120},
		{"name": "Bさん", "score": 95},
		{"name": "自分", "score": 110},
		{"name": "Cさん", "score": 80},
		{"name": "Dさん", "score": 60},
	]

	df = pd.DataFrame(participants)
	# 降順でソートして順位を付与
	df = df.sort_values(by="score", ascending=False).reset_index(drop=True)
	df["rank"] = df.index + 1

	# 自分の行を取得
	me_row = df[df["name"] == "自分"]
	if not me_row.empty:
		my_score = int(me_row.iloc[0]["score"])
		my_rank = int(me_row.iloc[0]["rank"])
	else:
		my_score = 0
		my_rank = "-"

	cols = st.columns([1, 2])
	cols[0].metric(label="あなたのスコア", value=my_score)
	cols[1].metric(label="あなたの順位", value=f"{my_rank} / {len(df)}")

	st.markdown("---")
	st.subheader("全参加者のランキング")

	# テーブル表示：順位・名前・スコア
	display_df = df[["rank", "name", "score"]].copy()
	display_df = display_df.rename(columns={"rank": "順位", "name": "名前", "score": "スコア"})

	# 表を出す（自分の行にマークをつける）
	def format_row(row):
		if row["名前"] == "自分":
			return f"**{row['名前']} (あなた)**"
		return row["名前"]

	# Streamlit では DataFrame の一部書式が限定されるので、表示用に変換してから書く
	disp = display_df.copy()
	disp["名前"] = disp.apply(format_row, axis=1)

	st.table(disp)


if __name__ == "__main__":
	main()

