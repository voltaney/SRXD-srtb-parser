"""ローカルにあるカスタムチャートを読み込む例"""

import itertools
import os
from pathlib import Path
from pprint import pprint

import srtb

app_data_path = os.getenv("APPDATA")
if app_data_path is None:
    raise ValueError("環境変数APPDATAが見つかりません")
default_custom_chart_dir = Path(app_data_path) / r"..\LocalLow\Super Spin Digital\Spin Rhythm XD\Custom"

chart_list = default_custom_chart_dir.glob("*.srtb")
for c in itertools.islice(chart_list, 10):
    with open(c, "r", encoding="utf-8") as f:
        chart = srtb.load(f)
    pprint(chart)
