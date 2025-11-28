import streamlit as st
import utils
import time
from datetime import datetime



# Safe initialization for Web3 manager (returns None on error)
@st.cache_resource
def get_web3_manager_safe():
	try:
		from data.fibase import Web3Manager

		return Web3Manager()
	except Exception as e:
		st.session_state.setdefault("_web3_init_error", str(e))
		return None


st.title("投票ページ 🗳️")

# 必要なセッション情報
user_id = st.session_state.get("user_id")
selected_market = st.session_state.get("selected_market")

if not user_id:
	st.warning("まずトップページでユーザーを選択してください。")
	st.stop()

# データ読み込み
data = utils.load_data()
users = data.get("users", {})
local_markets = data.get("markets", [])

web3_mgr = get_web3_manager_safe()

# on-chain markets (if any)
onchain_raw = []
if web3_mgr:
	try:
		onchain_raw = web3_mgr.get_all_markets() or []
	except Exception:
		onchain_raw = []


def normalize_onchain(m):
	try:
		end_ts = int(m.get("endTime") or 0)
	except Exception:
		end_ts = 0
	status = "closed" if m.get("resolved") else ("open" if (end_ts == 0 or end_ts > int(time.time())) else "closed")
	return {
		"id": str(m.get("id")),
		"title": m.get("title") or "タイトル未設定",
		"description": m.get("description", "") or "",
		"end_time": end_ts,
		"yes_bets": int(m.get("totalYes", 0)),
		"no_bets": int(m.get("totalNo", 0)),
		"status": status,
		"result": m.get("outcome") if m.get("resolved") else None,
		"source": "onchain",
	}


onchain_markets = [normalize_onchain(m) for m in onchain_raw]

for lm in local_markets:
	lm.setdefault("id", str(lm.get("id", "")))
	lm.setdefault("end_time", lm.get("end_datetime") or 0)
	lm.setdefault("source", lm.get("source", "local"))

# Merge markets: onchain takes priority
merged = {m["id"]: m for m in local_markets}
for m in onchain_markets:
	merged[m["id"]] = m
markets = list(merged.values())

# If no market is selected, ask user to choose
if not selected_market:
	st.info("投票するイベントをメイン画面から選んでください。\n(またはこのページで選択できます)")
	# show a dropdown to select
	options = [(m.get("id"), m.get("title")) for m in markets]
	if not options:
		st.warning("現在、投票可能なイベントがありません。")
		st.stop()

	sel = st.selectbox("投票するイベントを選ぶ", options=[(id, title) for id, title in options], format_func=lambda x: f"{x[0]} - {dict(options)[x[0]]}")
	if st.button("このイベントを選択して投票へ進む"):
		st.session_state["selected_market"] = sel[0] if isinstance(sel, tuple) else sel
		st.experimental_rerun()

	st.stop()

# find selected market
mid = str(selected_market)
market = next((m for m in markets if str(m.get("id")) == mid), None)
if not market:
	st.error("選択したイベントが見つかりません。メイン画面に戻ってもう一度選んでください。")
	st.stop()

st.header(f"投票：{market.get('title')}")
if market.get("description"):
	st.write(market.get("description"))

# show status
if market.get("status") != "open":
	st.warning("このイベントはすでに締め切られています（投票不可）。")
	st.stop()

user = users.get(user_id)
if not user:
	st.error("ユーザー情報が見つかりません。トップページでユーザーを選び直してください。")
	st.stop()

st.write(f"所持ポイント: **{user.get('points', 0)} OCP**")

col1, col2 = st.columns(2)
with col1:
	choice = st.radio("どちらに投票しますか？", ("Yes", "No"), horizontal=True)
with col2:
	max_points = max(0, int(user.get("points", 0)))
	amount = st.number_input("投入ポイント", min_value=1, max_value=max_points if max_points>0 else 1, value=1, step=1)

st.markdown("---")

if st.button("投票する（送信）"):
	is_yes = True if choice == "Yes" else False
	# On-chain voting if source == onchain and web3 available
	if market.get("source") == "onchain" and web3_mgr:
		try:
			receipt = web3_mgr.vote(int(market.get("id")), is_yes, int(amount))
			st.success("オンチェーン投票が送信されました。トランザクションレシートを確認してください。")
			st.json({
				"tx_hash": receipt.transactionHash.hex() if hasattr(receipt, "transactionHash") else str(receipt)
			})
		except Exception as e:
			st.error(f"オンチェーン投票に失敗しました: {e}")
	else:
		# Local fallback: update JSON
		pts = int(user.get("points", 0))
		if amount > pts:
			st.error("所持ポイントが不足しています。")
		else:
			# register bet record
			bet = {
				"user": user_id,
				"market_id": market.get("id"),
				"choice": "yes" if is_yes else "no",
				"amount": int(amount),
				"ts": datetime.utcnow().isoformat()
			}
			data.setdefault("bets", []).append(bet)

			# deduct points
			users[user_id]["points"] = pts - int(amount)

			# increase aggregate
			# find market in local markets list and update
			for m in local_markets:
				if str(m.get("id")) == str(market.get("id")):
					if is_yes:
						m["yes_bets"] = int(m.get("yes_bets", 0)) + int(amount)
					else:
						m["no_bets"] = int(m.get("no_bets", 0)) + int(amount)
					break

			utils.save_data(data)
			st.success("投票を受け付けました！（ローカルデータに保存されました）")

	# 送信後は選択解除してメインに戻る
	st.session_state.pop("selected_market", None)
	st.experimental_rerun()

