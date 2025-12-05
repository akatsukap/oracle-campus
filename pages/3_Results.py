import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import streamlit as st
import pandas as p

from utils import load_data, save_data

# Web3 manager を安全にインポート（無ければ None にする）。
# ページは Web3 がなくても動くようにする（resolve はローカルフォールバックあり）。

from utils.web3_manager import web3_managert

def main():
	st.title("結果・ランキング")

	# データ読み込み
	data = load_data() or {}
	users = data.get("users", {})
	markets = data.get("markets", [])
	bets = data.get("bets", [])

	# セッションから選択ユーザーを取得（`app.py` で選択されていることを前提とする）
	user_id = st.session_state.get("user_id")
	if not user_id:
		st.error("セッションにユーザーが設定されていません。トップページでユーザーを選択してください。")
		st.stop()

	# ベースポイント
	base_points = int(users.get(user_id, {}).get("points", 0))

	# Web3 manager は必要時に初期化する（resolve のとき）
	web3_mgr = None

	# オンチェーン残高はデフォルト 0（最小限のオンチェーン依存）
	onchain_points = 0

	# ユーザーが獲得したスコア（bets の集計）
	# bets のフォーマットは自由に変わるので、'user' と 'amount' または 'reward' を参照する
	got_score = 0
	participated_market_ids = []
	for b in bets:
		try:
			if b.get("user") == user_id:
				# 優先して reward を使い、なければ amount を合計
				if "reward" in b and b.get("reward") is not None:
					got_score += int(b.get("reward", 0))
				else:
					got_score += int(b.get("amount", 0))
				participated_market_ids.append(str(b.get("market_id")))
		except Exception:
			continue

	total_score = base_points + got_score

	# 参加したイベント情報を取得
	participated_markets = [m for m in markets if str(m.get("id")) in participated_market_ids]

	# 参加者ランキングを作成（ローカルユーザー + サンプル他ユーザー）
	participants = []
	# まず database.json のユーザーを追加
	for uid, info in users.items():
		pts = int(info.get("points", 0))
		# このユーザーの bets による追加分も反映
		extra = 0
		for b in bets:
			if b.get("user") == uid:
				extra += int(b.get("reward", b.get("amount", 0) or 0))
		name = "自分" if uid == user_id else uid
		score = pts + extra
		# オンチェーン残高はここでは自動加算しない（必要なら resolve 時に参照）
		participants.append({"name": name, "score": score})

	# 追加で既存のサンプル参加者を入れておく（重複を避ける）
	sample = [
		{"name": "Aさん", "score": 120},
		{"name": "Bさん", "score": 95},
		{"name": "Cさん", "score": 80},
		{"name": "Dさん", "score": 60},
	]
	existing_names = {p["name"] for p in participants}
	for s in sample:
		if s["name"] not in existing_names:
			participants.append(s)

	# DataFrame にして順位付け
	df = pd.DataFrame(participants)
	df = df.sort_values(by="score", ascending=False).reset_index(drop=True)
	df["rank"] = df.index + 1

	# 自分の行を取得して表示
	me_row = df[df["name"] == "自分"]
	if not me_row.empty:
		my_score = int(me_row.iloc[0]["score"])
		my_rank = int(me_row.iloc[0]["rank"])
	else:
		# もし自分が participants にいない場合は計算した total_score を優先して表示
		my_score = total_score
		# 順位は計算し直す
		higher = (df["score"] > my_score).sum()
		my_rank = int(higher) + 1

	cols = st.columns([1, 2, 1])
	cols[0].metric(label="あなたのベースポイント", value=base_points)
	cols[1].metric(label="今回獲得したスコア", value=got_score)
	cols[2].metric(label="オンチェーン残高（未使用）", value=onchain_points)

	st.markdown("---")
	st.metric(label="合計スコア（ベース + 獲得）", value=total_score)
	st.metric(label="あなたの順位", value=f"{my_rank} / {len(df)}")

	st.markdown("---")
	st.subheader("今回参加したイベント")
	if participated_markets:
		for m in participated_markets:
			st.markdown(f"- **{m.get('title', 'タイトル未設定')}** （ID: {m.get('id')}） - ステータス: `{m.get('status')}`")
	else:
		st.write("このユーザーはまだイベントに参加していません。")

	st.markdown("---")
	st.subheader("全参加者のランキング")

	display_df = df[["rank", "name", "score"]].copy()
	display_df = display_df.rename(columns={"rank": "順位", "name": "名前", "score": "スコア"})

	# 自分の行を目立たせる表示
	def format_row(row):
		if row["名前"] == "自分":
			return f"**{row['名前']} (あなた)**"
		return row["名前"]

	disp = display_df.copy()
	disp["名前"] = disp.apply(format_row, axis=1)
	st.table(disp)

	# 開催中と終了済みイベントの表示
	st.markdown("---")
	st.subheader("開催中のイベント")
	# オンチェーン市場が取得できればマージして使う
	onchain_markets = []
	if web3_mgr:
		try:
			onchain_raw = web3_mgr.get_all_markets() or []
			# convert onchain struct to local format used in database.json
			for m in onchain_raw:
				status = "closed" if m.get("resolved") else "open"
				open_m = {
					"id": m.get("id"),
					"title": m.get("title"),
					"description": "",
					"status": status,
					"yes_bets": int(m.get("totalYes", 0)),
					"no_bets": int(m.get("totalNo", 0)),
					"result": m.get("outcome") if m.get("resolved") else None,
				}
				onchain_markets.append(open_m)
		except Exception as e:
			st.warning(f"オンチェーン市場の取得に失敗しました: {e}")

	# マージ（onchain を優先して表示）
	merged = {str(m.get("id")): m for m in markets}
	for m in onchain_markets:
		merged[str(m.get("id"))] = m
	all_markets = list(merged.values())

	open_markets = [m for m in all_markets if m.get("status") == "open"]
	if open_markets:
		for m in open_markets:
			st.markdown(f"- **{m.get('title', 'タイトル未設定')}** （ID: {m.get('id')}）")
	else:
		st.write("開催中のイベントはありません。")

	st.markdown("---")
	st.subheader("終了したイベント")
	closed_markets = [m for m in all_markets if m.get("status") == "closed"]
	if closed_markets:
		for m in closed_markets:
			st.markdown(f"- **{m.get('title', 'タイトル未設定')}** （ID: {m.get('id')}） - 結果: `{m.get('result', '未確定')}`")
	else:
		st.write("まだ終了したイベントはありません。")

	# 管理者用: 市場を確定するボタン（オンチェーン優先、失敗時はローカルでフォールバック）
	# シンプル実装: ユーザーID が 'admin' の場合のみ表示（必要なら条件を変更してください）
	if user_id == "admin":
		st.markdown("---")
		st.subheader("管理者操作: 市場の結果を確定")
		with st.expander("オンチェーンで市場を確定（resolve）"):
			mid = st.text_input("市場 ID を入力", key="resolve_mid")
			outcome = st.selectbox("結果を選択", ["yes", "no"], key="resolve_outcome")
			if st.button("確定（オンチェーン実行）"):
				if not mid:
					st.error("市場 ID を入力してください")
				else:
					try:
						if Web3Manager is None:
							st.warning("Web3 が利用できません。ローカルデータで確定します。")
							# ローカルフォールバック: markets を更新して保存
							for m in markets:
								if str(m.get("id")) == str(mid):
									m["status"] = "closed"
									m["result"] = outcome
							data["markets"] = markets
							save_data(data)
							st.success("ローカルデータで市場を確定しました（フォールバック）。")
							st.experimental_rerun()
						else:
							# Web3Manager を初期化して resolve_market を実行
							web3_mgr = Web3Manager()
							onchain_outcome = True if outcome == "yes" else False

							utils.resolve_market(self, market_id, outcome)
							st.write("結果:", result)
							st.success(f"オンチェーンでの確定リクエスト送信完了: {str(receipt)}")
							# ローカルにも状態を反映しておく
							for m in markets:
								if str(m.get("id")) == str(mid):
									m["status"] = "closed"
									m["result"] = outcome
							data["markets"] = markets
							save_data(data)
							st.experimental_rerun()
					except Exception as e:
						st.error(f"市場確定に失敗しました: {e}")


if __name__ == "__main__":
	main()

