"""Spin Rhythm XDの譜面ファイルsrtbのパーサ

メタデータのみに対応しています。譜面データの読み込みは行われません。
"""

from srtb import parser

load = parser.load
