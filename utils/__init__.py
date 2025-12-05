"""utils パッケージの初期化。

このプロジェクトにはルートに `utils.py`（モジュール）と `utils/`（パッケージ）が共存します。
`from utils import load_data` などの呼び出しをパッケージ経由で動かせるよう、
ルートの `utils.py` をロードして必要な関数をエクスポートします。
"""
import os
import importlib.util

_root_utils_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "utils.py")

try:
	spec = importlib.util.spec_from_file_location("_root_utils", _root_utils_path)
	_root_utils = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(_root_utils)

	# 公開する関数をエクスポートする
	load_data = _root_utils.load_data
	save_data = _root_utils.save_data
	init_sample_data = getattr(_root_utils, "init_sample_data", None)
except Exception:
	# 何か失敗してもインポート時に例外を投げない（既存の用途で try/except しているため）
	pass
