"""Srtbファイルのパース処理の定義

loadメソッドを使うことで、Srtbクラスでパース結果を得られる。
"""

# main.py
import json
from dataclasses import dataclass, field
from typing import TextIO


@dataclass(kw_only=True)
class ChartDifficulty:
    """チャート難度を表現するクラス"""

    is_defined: bool = False
    level: int = 0


@dataclass(kw_only=True)
class Srtb:
    """Srtb構造を表現するクラス"""

    # チャートメタ情報
    track_title: str
    track_subtitle: str = ""
    track_artist: str
    charter: str
    # 難易度
    easy_difficulty: ChartDifficulty = field(default_factory=lambda: ChartDifficulty())
    normal_difficulty: ChartDifficulty = field(default_factory=lambda: ChartDifficulty())
    hard_difficulty: ChartDifficulty = field(default_factory=lambda: ChartDifficulty())
    expert_difficulty: ChartDifficulty = field(default_factory=lambda: ChartDifficulty())
    xd_difficulty: ChartDifficulty = field(default_factory=lambda: ChartDifficulty())
    # ファイルメタ情報
    asset_name: str
    file_created: int = 0

    def set_difficulty(self, difftype: int, diffrate: int) -> None:
        """srtbファイルの難易度を登録する

        Args:
            difftype (int): srtbフォーマットのdifficultyType
            diffrate (int): srtbフォーマットのdifficultyRate
        """
        difftype_map = {
            2: self.easy_difficulty,
            3: self.normal_difficulty,
            4: self.hard_difficulty,
            5: self.expert_difficulty,
            6: self.xd_difficulty,
        }
        if difftype in difftype_map:
            difftype_map[difftype].is_defined = True
            difftype_map[difftype].level = diffrate


def load(srtb_file: TextIO) -> Srtb:
    """_summary_

    Args:
        srtb_file (TextIO): srtbファイルのファイルディスクリプタ

    Returns:
        Srtb: パース結果
    """
    whole_data = json.load(srtb_file)
    trackinfo = dict()
    for v in whole_data["largeStringValuesContainer"]["values"]:
        if v["key"].startswith(("SO_TrackInfo", "SO_ClipInfo")):
            trackinfo[v["key"]] = json.loads(v["val"])
        elif v["key"].startswith("SO_TrackData"):
            # sometrack has usuless value
            if v["val"] == "null":
                continue
            # avoid parse whole track notes
            trackdata_meta_json = v["val"].split(',"notes":')[0] + "}"
            trackinfo[v["key"]] = json.loads(trackdata_meta_json)

    srtb = Srtb(
        track_title=trackinfo["SO_TrackInfo_TrackInfo"]["title"],
        track_artist=trackinfo["SO_TrackInfo_TrackInfo"]["artistName"],
        charter=trackinfo["SO_TrackInfo_TrackInfo"]["charter"],
        asset_name=trackinfo["SO_TrackInfo_TrackInfo"]["albumArtReference"]["assetName"],
    )
    if "subtitle" in trackinfo["SO_TrackInfo_TrackInfo"]:
        srtb.track_subtitle = trackinfo["SO_TrackInfo_TrackInfo"]["subtitle"]

    for diff_meta in trackinfo["SO_TrackInfo_TrackInfo"]["difficulties"]:
        # compatibleのチェック
        if "_active" in diff_meta and not diff_meta["_active"]:
            continue
        trackdata_name = diff_meta["assetName"]
        trackdata = trackinfo[f"SO_TrackData_{trackdata_name}"]
        # 難易度レベル
        diffrate = 0
        if "difficultyRating" in trackdata:
            diffrate = trackdata["difficultyRating"]
        srtb.set_difficulty(trackdata["difficultyType"], diffrate)

    return srtb
