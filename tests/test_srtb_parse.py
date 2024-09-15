import os
import random
from pathlib import Path

import pytest
from tqdm import tqdm

import srtb


def test_no_exceptions() -> None:
    try:
        app_data_path = os.getenv("APPDATA")
        if app_data_path is None:
            raise ValueError("環境変数APPDATAが見つかりません")
        default_custom_chart_dir = Path(app_data_path) / r"..\LocalLow\Super Spin Digital\Spin Rhythm XD\Custom"
        chart_list = list(default_custom_chart_dir.glob("*.srtb"))
        for c in tqdm(random.sample(chart_list, 100)):
            with open(c, "r", encoding="utf-8") as f:
                chart = srtb.load(f)
            chart.read_clip_metadata()
    except Exception as e:
        pytest.fail(f"An unexpected exception was raised: {e}")
