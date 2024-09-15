"""Srtbファイルのパース処理の定義

loadメソッドを使うことで、Srtbクラスでパース結果を得られる。
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis

import srtb.exceptions as custom_exceptions


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


def read_metainfo_from_srtb_file(srtb_file: TextIO) -> dict:
    """srtbファイルをJSON形式にパースする

    Args:
        srtb_file (TextIO): srtbファイルのファイルオブジェクト

    Raises:
        srtb.exceptions.SrtbJsonFormatError: srtbファイルのJSONデコードに失敗した場合
        srtb.exceptions.SrtbKeyError: srtbファイルに必要なパラメータが存在しない場合

    Returns:
        dict: srtbファイルのメタ情報
    """
    try:
        whole_data = json.load(srtb_file)
    except json.JSONDecodeError as e:
        raise custom_exceptions.SrtbJsonFormatError("Srtbファイル全体はJSON形式である必要があります") from e
    trackinfo = dict()
    try:
        for v in whole_data["largeStringValuesContainer"]["values"]:
            if not isinstance(v, dict) or "key" not in v:
                # 値がdictでかつkeyというキーが存在しないならスキップ
                continue
            if v["key"].startswith(("SO_TrackInfo", "SO_ClipInfo")):
                # 基本的なチャート情報
                trackinfo[v["key"]] = json.loads(v["val"])
            elif v["key"].startswith("SO_TrackData"):
                # 難易度情報
                if v["val"] == "null":
                    # 情報が無い場合はスキップ
                    continue
                # 譜面内容のパースは不要なので、メタ情報のみ取得
                trackdata_meta_json = v["val"].split(',"notes":')[0] + "}"
                trackinfo[v["key"]] = json.loads(trackdata_meta_json)
    except KeyError as e:
        raise custom_exceptions.SrtbKeyError("Srtbファイルに必要なパラメータが存在しません") from e
    except json.JSONDecodeError as e:
        raise custom_exceptions.SrtbJsonFormatError("Srtbファイルの特定の子要素もJSON形式である必要があります") from e

    return trackinfo


def create_srtb_from_metainfo(trackinfo: dict, srtb_file_path: Path) -> Srtb:
    """srtbファイルのメタ情報からSrtbクラスを生成する

    Args:
        trackinfo (dict): srtbファイルのメタ情報
        srtb_file_path (Path): srtbファイルのパス

    Returns:
        Srtb: Srtbクラス
    """
    # Srtbクラスを初期化
    srtb = Srtb(
        track_title=trackinfo["SO_TrackInfo_TrackInfo"]["title"],
        track_artist=trackinfo["SO_TrackInfo_TrackInfo"]["artistName"],
        charter=trackinfo["SO_TrackInfo_TrackInfo"]["charter"],
        albumart_asset_name=trackinfo["SO_TrackInfo_TrackInfo"]["albumArtReference"]["assetName"],
        clip_asset_name=trackinfo["SO_ClipInfo_ClipInfo_0"]["clipAssetReference"]["assetName"],
        self_path=srtb_file_path.resolve(),
        file_reference=srtb_file_path.resolve().stem,
    )

    # サブタイトルが存在する場合は設定
    if "subtitle" in trackinfo["SO_TrackInfo_TrackInfo"]:
        srtb.track_subtitle = trackinfo["SO_TrackInfo_TrackInfo"]["subtitle"]

    # 難易度情報を登録
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


def load(srtb_file: TextIO) -> Srtb:
    """srtbファイルを読み込み、Srtbクラスを生成する

    Args:
        srtb_file (TextIO): srtbファイルのファイルオブジェクト

    Raises:
        custom_exceptions.SrtbKeyError: srtbファイルに必要なパラメータが存在しない場合

    Returns:
        Srtb: Srtbクラス
    """
    # srtbファイルからメタ情報を読み込む
    trackinfo = read_metainfo_from_srtb_file(srtb_file)
    try:
        # メタ情報からSrtbクラスを生成
        srtb = create_srtb_from_metainfo(trackinfo, Path(srtb_file.name))
    except KeyError as e:
        raise custom_exceptions.SrtbKeyError("Srtbファイルに必要なパラメータが存在しません") from e

    return srtb
