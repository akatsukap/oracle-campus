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
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # コントラクトの準備
        # utils/abi.json の絶対パスを作成
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # utils フォルダ
        ABI_PATH = os.path.join(BASE_DIR, "abi.json")

        with open(ABI_PATH, "r") as f:
            abi = json.load(f)
        self.contract = self.w3.eth.contract(
            address=os.getenv("CONTRACT_ADDRESS"), 
            abi=abi
        )

        #【追加】SBTコントラクトの読み込み
        # SBTのアドレスとABIをここに直接書くか、.envに追加して読み込む
        
        sbt_address = "0x6AF471Be518c3C73A9aB83669f791D80e6B8Ea62"

        sbt_abi_path = os.path.join(current_dir, 'sbt_abi.json')

        if os.path.exists(sbt_abi_path):
            with open(sbt_abi_path, "r") as f:
                sbt_abi = json.load(f)
            self.sbt_contract = self.w3.eth.contract(address=sbt_address, abi=sbt_abi)
        else:
            print("⚠️ SBT ABI file not found!")
        
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

    def get_balance(self):
        """自分のOCP残高を確認する"""
        return self.contract.functions.balances(self.account.address).call()

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

    #【追加】SBTを持っているか確認する関数
    def has_sbt(self, user_address):
        try:
            balance = self.sbt_contract.functions.balanceOf(user_address).call()
            return balance > 0
        except Exception as e:
            print(f"SBT Check Error: {e}")
            return False

    #【追加】SBTを発行する関数（管理者権限で実行）
    def mint_sbt(self, target_user_address):
        print(f"Minting SBT to {target_user_address}")
        return self._send_transaction(
            self.sbt_contract.functions.safeMint(target_user_address)
        )
    
    def get_my_balance(self):
        """自分のOCP残高を確認する（旧関数名）"""
        return self.contract.functions.balances(self.account.address).call()
