import streamlit as st
import time
from datetime import datetime
import os
import sys
from dotenv import load_dotenv
import style_config as sc

#デザイン統一
sc.apply_common_style()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------_
# 🔒 ① ここにアクセス制限を追加！
# ---------------------------------------------
st.set_page_config(page_title="投票画面", layout="wide", page_icon="🗳️")

# セッションから現在のユーザーIDを取得
user_id = st.session_state.get("user_id")

# admin以外なら追い出す
if user_id == "admin":
    st.error("⛔️ アクセス権限がありません！")
    st.warning("このページはユーザー専用です。サイドバーから他のページに移動してください。")
    st.stop()  # ←これで処理を強制終了させる
load_dotenv()

# ═══════════════════════════════════════════════════════════════
# ブロックチェーン専用版 Vote.py
# オンチェーンのみで動作、database.json は使用しない
# ═══════════════════════════════════════════════════════════════

# Web3Manager を安全に初期化
@st.cache_resource
def get_web3_manager_safe():
	try:
		from utils.web3_manager import Web3Manager
		mgr = Web3Manager()
		return mgr, None  # (manager, error)
	except Exception as e:
		return None, str(e)

st.title("🗳️投票ページ ")

# ─────────────────────────────
# 接続状態を表示
# ─────────────────────────────
web3_mgr, web3_error = get_web3_manager_safe()

# 接続状態インジケーター
if web3_mgr:
	try:
		is_connected = web3_mgr.w3.is_connected()
		account_addr = web3_mgr.account.address
		balance = web3_mgr.get_balance()
		
		# 接続成功時の表示
		col1, col2, col3 = st.columns(3)
		with col1:
			st.metric("ブロックチェーン", "✅ 接続中")
		with col2:
			st.metric("ネットワーク", "Sepolia")
		with col3:
			st.metric("所持ポイント", f"{balance} OCP")
		
		st.info(f"ウォレット: `{account_addr}`")
		
	except Exception as e:
		st.error(f"❌ 接続情報取得エラー: {e}")
		st.stop()
else:
	st.error(f"❌ ブロックチェーン接続失敗")
	st.error(f"エラー詳細: {web3_error}")
	st.info("""
	以下を確認してください：
	1. `.env` ファイルに以下を設定
	   - WEB3_RPC_URL: Sepolia RPC URL
	   - PRIVATE_KEY: ウォレットの秘密鍵
	   - CONTRACT_ADDRESS: デプロイされたコントラクトアドレス
	2. `abi.json` がプロジェクトルートに存在
	3. web3.py, python-dotenv がインストール済み
	""")
	st.stop()

st.divider()

# ─────────────────────────────
# ブロックチェーンから市場データ取得
# ─────────────────────────────
with st.spinner("ブロックチェーンから市場情報を取得中…"):
	try:
		markets = web3_mgr.get_all_markets() or []
	except Exception as e:
		st.error(f"市場データ取得エラー: {e}")
		st.stop()

if not markets:
	st.warning("現在、投票可能なイベントがありません。")
	st.stop()

# ─────────────────────────────
# マーケット選択
# ─────────────────────────────
# ─────────────────────────────
# マーケット選択
# ─────────────────────────────
selected_market = st.session_state.get("selected_market")

if not selected_market:
	st.subheader("📍 投票するイベントを選択")
	
	# デバッグ: 最初のマーケット情報を表示
	with st.expander("🔍 デバッグ：マーケットデータ構造"):
		if markets:
			st.json(markets[0])
	
	options = []
	for m in markets:
		now_ts = int(time.time())
		for m in markets:
			# 除外条件: すでに resolved のもの
			if m.get("resolved"):
				continue
			# 除外条件: endTime が設定されていて締め切りを過ぎているもの
			try:
				end_ts = int(m.get("endTime", 0) or 0)
			except Exception:
				end_ts = 0
			if end_ts != 0 and end_ts <= now_ts:
				# 締め切りを過ぎているため選択肢に含めない
				continue
			# 表示ラベル作成
			title = m.get('title', 'タイトル未設定')
			yes_total = m.get('totalYes', 0)
			no_total = m.get('totalNo', 0)
			option_label = f"{title} (Yes: {yes_total} / No: {no_total} OCP)"
			options.append((str(m.get("id")), option_label))
	
	if not options:
		st.warning("現在、投票受付中のイベントはありません。")
		st.stop()
	
	sel = st.selectbox(
		"投票するイベント",
		options=options,
		format_func=lambda x: x[1]
	)
	
	if st.button("このイベントを選択"):
		st.session_state["selected_market"] = sel[0]
		st.rerun()
	
	st.stop()

# ─────────────────────────────
# 選択したマーケット詳細表示
# ─────────────────────────────
mid = str(selected_market)
market = next((m for m in markets if str(m.get("id")) == mid), None)

if not market:
	st.error("選択したイベントが見つかりません。")
	st.session_state.pop("selected_market", None)
	st.rerun()

# マーケット情報
st.header(f"投票：{market.get('title')}")
if market.get("description"):
	st.write(market.get("description"))

# 終了時間チェック
end_time = int(market.get("endTime", 0))
now_ts = int(time.time())
is_open = not market.get("resolved") and (end_time == 0 or end_time > now_ts)

if not is_open:
	st.warning("❌ このイベントは締め切られています（投票不可）。")
	if st.button("戻る"):
		st.session_state.pop("selected_market", None)
		st.rerun()
	st.stop()

st.success("✅ 投票受付中です")

# 投票結果表示
col1, col2 = st.columns(2)
with col1:
	st.metric("Yes 投票合計", f"{market.get('totalYes', 0)} OCP")
with col2:
	st.metric("No 投票合計", f"{market.get('totalNo', 0)} OCP")

# Yes率表示
total_pool = int(market.get('totalYes', 0) or 0) + int(market.get('totalNo', 0) or 0)
if total_pool > 0:
	yes_ratio = int(market.get('totalYes', 0) or 0) / total_pool
	st.progress(yes_ratio, text=f"Yes率: {int(yes_ratio * 100)}%")
else:
	st.text("まだ投票がありません")

st.divider()

# ─────────────────────────────
# 投票フォーム
# ─────────────────────────────
st.subheader("🗳️ 投票する")

col1, col2 = st.columns(2)
with col1:
	choice = st.radio("投票内容", ("Yes", "No"), horizontal=True)
with col2:
	amount = st.number_input("投入ポイント", min_value=1, value=10, step=1)

# ─────────────────────────────
# 投票送信ボタン
# ─────────────────────────────
if st.button("投票する（トランザクション送信）", type="primary"):
	is_yes = choice == "Yes"
	
	with st.spinner("🔄 ブロックチェーンにトランザクションを送信中…"):
		try:
			receipt = web3_mgr.vote(int(market.get("id")), is_yes, int(amount))
			
			# トランザクションハッシュ取得
			tx_hash = receipt.transactionHash.hex() if hasattr(receipt, "transactionHash") else str(receipt)
			
			st.success("✅ 投票がブロックチェーンに記録されました！")
			
			st.json({
				"トランザクションハッシュ": tx_hash,
				"マーケットID": market.get("id"),
				"投票内容": choice,
				"投入ポイント": amount,
				"ステータス": "成功"
			})
			
			# Etherscan リンク表示
			etherscan_url = f"https://sepolia.etherscan.io/tx/{tx_hash}"
			st.markdown(f"📍 **[Etherscan で トランザクションを確認]({etherscan_url})**")
			
			time.sleep(2)
			
			# 選択をリセット
			st.session_state.pop("selected_market", None)
			st.rerun()
			
		except Exception as e:
			st.error(f"❌ 投票に失敗しました")
			st.error(f"エラー詳細: {e}")

st.divider()

# ─────────────────────────────
# 戻るボタン
# ─────────────────────────────
if st.button("戻る"):
	st.session_state.pop("selected_market", None)
	st.rerun()

