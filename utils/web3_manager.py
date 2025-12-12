import json
import os
from web3 import Web3
from dotenv import load_dotenv


# .envを読み込む
load_dotenv()


class Web3Manager:
    def __init__(self):
        # ブロックチェーンに接続
        self.w3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_RPC_URL")))
        self.account = self.w3.eth.account.from_key(os.getenv("PRIVATE_KEY"))
        self.chain_id = 11155111 # Sepoliaの場合


        # コントラクトの準備: プロジェクト内の候補パスから ABI を探して読み込む
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        candidate_paths = [
            os.path.join(BASE_DIR, "abi.json"),
            os.path.join(os.path.dirname(BASE_DIR), "utils", "abi.json"),
            os.path.join(os.getcwd(), "utils", "abi.json"),
            os.path.join(os.getcwd(), "abi.json"),
        ]


        abi = None
        abi_path_used = None
        for p in candidate_paths:
            try:
                if p and os.path.exists(p):
                    with open(p, "r", encoding="utf-8") as f:
                        abi = json.load(f)
                    abi_path_used = p
                    break
            except Exception:
                continue


        if abi is None:
            raise FileNotFoundError(
                "abi.json が見つかりません。プロジェクトの `utils/abi.json` またはルートの `abi.json` を配置してください。"
            )
       
        print(f"✅ ABI loaded from: {abi_path_used}")
        self.contract = self.w3.eth.contract(
            address=os.getenv("CONTRACT_ADDRESS"),
            abi=abi
        )
       
        print(f"Connected to Web3: {self.w3.is_connected()}")


    def _send_transaction(self, func_call):
        """トランザクションを作って、署名して、送る共通関数"""
        nonce = self.w3.eth.get_transaction_count(self.account.address)
       
        # ガス代の見積もり（少し多めに設定）
        tx_data = func_call.build_transaction({
            'chainId': self.chain_id,
            'gas': 2000000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
        })
       
        # 署名
        signed_tx = self.w3.eth.account.sign_transaction(tx_data, private_key=os.getenv("PRIVATE_KEY"))
       
        # 送信
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
       
        # 完了を待つ
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt


    # --- みんなが使う関数 ---


    def get_balance(self, address: str = None):
        """指定アドレス（なければ自身）の OCP 残高を確認する"""
        target = address or self.account.address
        return self.contract.functions.balances(target).call()


    def get_user_bet(self, address: str, market_id: int):
        """特定ユーザーの特定マーケットへのベット情報を取得"""
        try:
            bet = self.contract.functions.bets(address, market_id).call()
            # bet は (amount, isYes, claimed) のタプル
            return {
                "amount": int(bet[0]),
                "isYes": bool(bet[1]),
                "claimed": bool(bet[2])
            }
        except Exception:
            return {"amount": 0, "isYes": False, "claimed": False}


    def get_all_user_bets(self, address: str):
        """指定ユーザーの全マーケットへのベット情報を取得"""
        bets = []
        try:
            market_count = self.contract.functions.marketCount().call()
            for market_id in range(market_count):
                bet_info = self.get_user_bet(address, market_id)
                if bet_info["amount"] > 0:
                    bets.append({
                        "market_id": market_id,
                        "amount": bet_info["amount"],
                        "isYes": bet_info["isYes"],
                        "claimed": bet_info["claimed"]
                    })
        except Exception:
            pass
        return bets


    def faucet(self):
        """1000ポイントもらう"""
        return self._send_transaction(self.contract.functions.faucet())


    def create_market(self, title, duration_sec=3600):
        """市場を作る(Admin)"""
        return self._send_transaction(
            self.contract.functions.createMarket(title, duration_sec)
        )


    def vote(self, market_id, is_yes, amount):
        """投票する"""
        return self._send_transaction(
            self.contract.functions.vote(market_id, is_yes, amount)
        )
       
    def resolve_market(self, market_id, outcome):
        """結果を確定する(Admin)"""
        return self._send_transaction(
            self.contract.functions.resolveMarket(market_id, outcome)
        )
       
    def claim_reward(self, market_id):
        """配当をもらう"""
        return self._send_transaction(
            self.contract.functions.claimReward(market_id)
        )


    def get_all_markets(self):
        """全市場データを取得して辞書のリストで返す"""
        count = self.contract.functions.marketCount().call()
        markets = []
        for i in range(count):
            # Solidityのstructはタプル(リストみたいなもの)で返ってくる
            m = self.contract.functions.markets(i).call()
            markets.append({
                "id": m[0],
                "title": m[1],
                "endTime": m[2],
                "totalYes": m[3],
                "totalNo": m[4],
                "resolved": m[5],
                "outcome": m[6]
            })
        return markets


