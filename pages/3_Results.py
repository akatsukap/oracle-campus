import time
from typing import Dict, List

import pandas as pd
import streamlit as st


@st.cache_resource
def get_web3_manager_safe():
    """Create Web3Manager with caching; return None when setup fails."""
    try:
        from utils.web3_manager import Web3Manager

        return Web3Manager()
    except Exception as exc:  # noqa: BLE001
        st.session_state.setdefault("_web3_init_error", str(exc))
        return None


def _normalize_market(raw: Dict) -> Dict:
    """Convert contract market dict into a uniform shape used in the UI."""
    try:
        end_ts = int(raw.get("endTime") or 0)
    except Exception:  # noqa: BLE001
        end_ts = 0

    now_ts = int(time.time())
    if raw.get("resolved"):
        status = "closed"
    elif end_ts == 0 or end_ts > now_ts:
        status = "open"
    else:
        status = "closed"

    return {
        "id": str(raw.get("id")),
        "title": raw.get("title") or "タイトル未設定",
        "end_time": end_ts,
        "yes_bets": int(raw.get("totalYes", 0)),
        "no_bets": int(raw.get("totalNo", 0)),
        "status": status,
        "result": raw.get("outcome") if raw.get("resolved") else None,
    }


def _pull_markets(web3_mgr) -> List[Dict]:
    if not web3_mgr:
        return []
    try:
        onchain_raw = web3_mgr.get_all_markets() or []
    except Exception as exc:  # noqa: BLE001
        st.warning(f"オンチェーン市場の取得に失敗しました: {exc}")
        return []
    return [_normalize_market(m) for m in onchain_raw]


def _parse_address_lines(raw: str) -> List[str]:
    addrs = []
    for line in raw.splitlines():
        addr = line.strip()
        if addr:
            addrs.append(addr)
    return addrs


st.title("結果・ランキング")

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("トップページでユーザーを選択してください。")
    st.stop()

web3_mgr = get_web3_manager_safe()

status_col1, status_col2 = st.columns(2)
with status_col1:
    if web3_mgr and web3_mgr.w3.is_connected():
        st.success("Web3 接続中 ✅")
    else:
        st.error("Web3 接続に失敗しました。環境変数と ABI を確認してください。")
        if st.session_state.get("_web3_init_error"):
            st.caption(st.session_state.get("_web3_init_error"))

with status_col2:
    pass

if not web3_mgr:
    st.stop()

with st.spinner("オンチェーンから市場データを取得中..."):
    markets = _pull_markets(web3_mgr)

open_markets = [m for m in markets if m.get("status") == "open"]
closed_markets = [m for m in markets if m.get("status") == "closed"]

total_volume = sum(m.get("yes_bets", 0) + m.get("no_bets", 0) for m in markets)

metric_cols = st.columns(3)
metric_cols[0].metric("開催中の市場", len(open_markets))
metric_cols[1].metric("終了した市場", len(closed_markets))
metric_cols[2].metric("合計プールサイズ", total_volume)

st.markdown("---")

# 自分のアドレスと残高表示
my_address = web3_mgr.account.address
current_balance = web3_mgr.get_balance()
st.metric("現在の所持ポイント", f"{current_balance} OCP")

st.divider()

# 配当の受け取り（Claim）
st.subheader("💰 配当を受け取る")

# 解決済み（結果が出た）市場を取得
closed_markets_list = [m for m in markets if m.get("status") == "closed"]

if not closed_markets_list:
    st.info("終了したイベントはまだありません。")
else:
    # ドロップダウンで選択
    options = {str(m.get("id")): f"{m.get('title')} (結果: {'Yes' if m.get('result') else 'No'})" for m in closed_markets_list}
    selected_id = st.selectbox("結果が出たイベントを選択", options.keys(), format_func=lambda x: options[x])

    if st.button("配当を請求する (Claim Reward)"):
        with st.spinner("ブロックチェーンを確認中..."):
            try:
                # スマートコントラクトを実行
                receipt = web3_mgr.claim_reward(int(selected_id))
                
                st.balloons()
                st.success("🎉 配当を受け取りました！")
                tx_hash = getattr(receipt, 'transactionHash', None)
                if tx_hash:
                    st.markdown(f"Tx Hash: `{tx_hash.hex()}`")
                
                # 残高が増えたことを確認するためにリロード
                time.sleep(2)
                st.rerun()
                
            except Exception as e:
                st.error("受け取り失敗（または既に受け取り済み/外れ）")
                st.error(f"詳細: {e}")

st.markdown("---")
st.subheader("ウォレット別ランキング（残高順）")

default_block = getattr(web3_mgr.account, "address", "")
address_block = default_block

addresses = set(_parse_address_lines(address_block))
if default_block:
    addresses.add(default_block)

rows = []
for addr in addresses:
    try:
        bal = web3_mgr.get_balance(addr)
        bets = web3_mgr.get_all_user_bets(addr)
        total_staked = sum(int(b.get("amount", 0)) for b in bets)
        rows.append(
            {
                "address": addr,
                "balance": bal,
                "active_bets": len(bets),
                "total_staked": total_staked,
            }
        )
    except Exception as exc:  # noqa: BLE001
        st.warning(f"{addr} の取得に失敗しました: {exc}")

if rows:
    df_rank = pd.DataFrame(rows)
    df_rank = df_rank.sort_values(by=["balance", "total_staked"], ascending=False).reset_index(drop=True)
    df_rank.insert(0, "rank", df_rank.index + 1)
    st.dataframe(
        df_rank,
        use_container_width=True,
        hide_index=True,
        column_config={
            "balance": st.column_config.NumberColumn("残高 (OCP)", format="%d"),
            "total_staked": st.column_config.NumberColumn("累計ベット額", format="%d"),
            "active_bets": st.column_config.NumberColumn("ベット件数"),
        },
    )
else:
    st.info("ランキング対象のウォレットがありません。")

st.markdown("---")
st.subheader("市場の結果とプールランキング")

if not markets:
    st.info("オンチェーン市場がまだありません。")
else:
    top_by_pool = sorted(
        markets,
        key=lambda m: m.get("yes_bets", 0) + m.get("no_bets", 0),
        reverse=True,
    )
    st.caption("プール=Yes/Noに積まれたOCPの合計です。")
    pool_df = pd.DataFrame(
        [
            {
                "title": m.get("title"),
                "status": m.get("status"),
                "result": m.get("result", "未確定"),
                "pool": m.get("yes_bets", 0) + m.get("no_bets", 0),
                "yes": m.get("yes_bets", 0),
                "no": m.get("no_bets", 0),
            }
            for m in top_by_pool
        ]
    )
    st.dataframe(
        pool_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "pool": st.column_config.NumberColumn("プール合計", format="%d"),
            "yes": st.column_config.NumberColumn("Yes", format="%d"),
            "no": st.column_config.NumberColumn("No", format="%d"),
        },
    )