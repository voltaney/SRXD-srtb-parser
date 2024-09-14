"""Srtbファイルのパース処理の定義

loadメソッドを使うことで、Srtbクラスでパース結果を得られる。
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis


@dataclass(kw_only=True)
class ChartDifficulty:
    """チャート難度を表現するクラス"""

    is_defined: bool = False
    level: int = 0


@dataclass(kw_only=True)
class Srtb:
    """Srtbファイルの情報を保持するクラス

    Args:
        track_title (str): 曲名
        track_subtitle (str): サブタイトル
        track_artist (str): アーティスト名
        charter (str): チャーター名
        easy_difficulty (ChartDifficulty): Easy難易度
        normal_difficulty (ChartDifficulty): Normal難易度
        hard_difficulty (ChartDifficulty): Hard難易度
        expert_difficulty (ChartDifficulty): Expert難易度
        xd_difficulty (ChartDifficulty): XD難易度
        albumart_asset_name (str): アルバムアートのアセット名
        clip_asset_name (str): クリップのアセット名
        self_path (Path): 自身のファイルパス
        filereference (str): ファイルリファレンス(Spinshareの参照に利用可能)
        clip_duration (int): クリップの再生時間(秒)
    """

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
    albumart_asset_name: str
    clip_asset_name: str
    self_path: Path
    file_reference: str
    # クリップファイル
    clip_duration: int | None = None

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

    def read_clip_metadata(self) -> None:
        """clipのメタデータを読み込む"""
        audio_clip_dir = "AudioClips"
        clip_file = self.self_path.parent / audio_clip_dir / f"{self.clip_asset_name}.mp3"
        if not clip_file.exists():
            clip_file = self.self_path.parent / audio_clip_dir / f"{self.clip_asset_name}.ogg"
        if clip_file.exists():
            if clip_file.suffix == ".mp3":
                mp3_audio = MP3(str(clip_file))
                self.clip_duration = int(mp3_audio.info.length)  # type: ignore
            elif clip_file.suffix == ".ogg":
                ogg_audio = OggVorbis(str(clip_file))
                self.clip_duration = int(ogg_audio.info.length)  # type: ignore
            else:
                self.clip_duration = None
        else:
            self.clip_duration = None


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
        if not isinstance(v, dict) or "key" not in v:
            # vがdictでかつkeyが存在しないならスキップ
            continue
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
        albumart_asset_name=trackinfo["SO_TrackInfo_TrackInfo"]["albumArtReference"]["assetName"],
        clip_asset_name=trackinfo["SO_ClipInfo_ClipInfo_0"]["clipAssetReference"]["assetName"],
        self_path=Path(srtb_file.name).resolve(),
        file_reference=Path(srtb_file.name).resolve().stem,
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
