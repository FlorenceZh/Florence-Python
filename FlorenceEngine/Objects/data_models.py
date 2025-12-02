from dataclasses import dataclass
from typing import List, Optional
import numpy as np


@dataclass
class Time:
    """时间结构体，相对乐句开始为0基准"""
    start: int  # 音符开始的时间点，单位为ms
    end: int    # 音符结束的时间点，单位为ms


@dataclass
class Word:
    """最小单位，来自musicXML中的音符"""
    pitch: float        # 音高频率（Hz）
    time: Time          # 时间结构体
    lrc: str            # 歌词拼音，若musicXML输入的为中文则转成拼音，忽略声调
    oriWave: Optional[np.ndarray] = None  # FlorenceSpeakGenerateor合成的原始tts二进制数据
    pitchedWave: Optional[np.ndarray] = None #音高调整后的二进制数据


@dataclass
class Section:
    """乐段"""
    wordList: List[Word]    # 包含本乐段所有word的列表，创建时应检查音符没有重叠
    sectionStart: int       # 本乐段开始时间，0基准为歌曲开头，单位ms
    sectionSrc: Optional[np.ndarray] = None  # 链接oriWave合成的二进制数据


@dataclass
class Track:
    """整个音轨"""
    sectionList: List[Section]    # 同wordList
    trackWaveData: Optional[np.ndarray] = None  # 一个numpy向量，储存着合成好的整个音轨音频


@dataclass
class Song:
    """整个歌曲"""
    trackList: List[Track]      # 同wordList
    name: str                   # 输入musicXML的文件名称
    waveData: Optional[np.ndarray] = None  # 一个numpy向量，储存着合成好的整个歌曲音频