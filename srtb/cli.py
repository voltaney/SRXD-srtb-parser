"""CLI定義"""

import pprint

import fire

import srtb


def parse(filename: str) -> str:
    """srtbをパースした結果を文字列で返す

    Args:
        filename (str): srtbファイルのパス

    Returns:
        str: srtbの内容
    """
    with open(filename, "r", encoding="utf-8") as f:
        chart = srtb.load(f)
    return pprint.pformat(chart, indent=4)


def main() -> None:
    """CLIのエントリポイント"""
    fire.Fire(
        {
            "parse": parse,
        }
    )
