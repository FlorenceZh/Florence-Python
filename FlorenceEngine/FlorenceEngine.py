import os
import traceback
from typing import Optional

from FlorenceEngine.FlorenceScoreDecoder.FlorenceScoreDecoder import FlorenceScoreDecoder
from FlorenceEngine.FlorenceSpeakGenerateor.FlorenceSpeakGenerateor import FlorenceSpeakGenerateor
from FlorenceEngine.FlorenceCoder.FlorenceCoder import FlorenceCoder
from FlorenceEngine.FlorenceWaveConnecter.FlorenceWaveConnecter import FlorenceWaveConnecter
from FlorenceEngine.FlorenceOutputGenerater.FlorenceOutputGenerater import FlorenceOutputGenerater
from FlorenceEngine.Objects.Selector import selectScoreFile
from FlorenceEngine.Objects.context import Context


class FlorenceEngine:
    """
    Florence歌声合成引擎主控制器
    负责调度整个流水线：
    1. 解析乐谱 → 2. 语音合成 → 3. 音高校正 → 4. 平滑连接 → 5. 输出装配
    """

    def __init__(self,
                 output_dir: str = "output",
                 input_dir: str = "input",
                 sample_rate: int = 22050,
                 is_debug = True):
        """
        初始化Florence引擎

        Args:
            output_dir: 输出目录
            input_dir: 输入目录（用于文件选择器的默认目录）
            sample_rate: 音频采样率
        """
        self.output_dir = output_dir
        self.input_dir = input_dir
        self.sample_rate = sample_rate
        self.isDebug = is_debug

        context = Context(
            sample_rate=self.sample_rate,
            isDebug= self.isDebug
        )

        # 初始化各个模块
        print("正在初始化Florence歌声合成引擎...")
        self.decoder = FlorenceScoreDecoder(context)
        self.speech_generator = FlorenceSpeakGenerateor(context)
        # self.coder = FlorenceCoder(context)
        # self.wave_connector = FlorenceWaveConnecter(context)
        # self.output_generator = FlorenceOutputGenerater(
        #     output_dir=output_dir,
        #     sample_rate=sample_rate
        # )

    def select_and_process(self) -> Optional[str]:
        """
        提供文件选择器让用户选择乐谱文件，并处理整个工程

        Returns:
            生成的WAV文件路径，如果处理失败则返回None
        """
        # 使用文件选择器选择MusicXML文件
        if self.isDebug:
            score_file = ".//input//雪绒花.musicxml"
        else:
            score_file = selectScoreFile(self.get_engine_info()['input_directory'])
        
        if not score_file:
            print("用户取消文件选择")
            return None

        print(f"已选择文件：{score_file}")
        return self.process_score(score_file)

    def process_score(self, score_path: str) -> Optional[str]:
        """
        处理指定的MusicXML文件

        Args:
            score_path: MusicXML文件的路径

        Returns:
            生成的WAV文件路径，如果处理失败则返回None
        """
        print(f"开始处理乐谱文件：{score_path}")

        # 验证文件
        if not os.path.exists(score_path):
            raise FileNotFoundError(f"乐谱文件不存在：{score_path}")

        # step1: 解析乐谱
        print("step1: 解析MusicXML乐谱...")
        song = self._decode_score(score_path)
        print(f"乐谱解析完成，包含 {len(song.trackList)} 个音轨")

        # step2: 语音合成
        print("step2: 生成基础语音...")
        song = self._generate_speech(song)
        print("基础语音生成完成")

        # step3: 音高
        print("step3: 进行音高调整...")
        song = self._adjust_pitch(song)
        print("音高调整完成")

        # step4: 平滑连接
        print("step4: 连接音频段落...")
        song = self._smooth_connect(song)
        print("音频段落连接完成")

        # step5: 输出装配
        print("step5: 生成最终输出文件...")
        output_path = self._generate_output(song)
        print("最终输出文件生成完成")
        print(f"输出文件：{output_path}")

        return output_path

    def _decode_score(self, score_path: str):
        """阶段1：乐谱解析"""
        return self.decoder.decode_score(score_path)

    def _generate_speech(self, song):
        """阶段2：基础语音合成"""
        return self.speech_generator.generate_song_speech(song)

    def _adjust_pitch(self, song):
        """阶段3：音高校正"""
        try:
            return self.coder.process_song(song)
        except Exception as e:
            raise Exception(f"音高校正失败：{e}")

    def _smooth_connect(self, song):
        """阶段4：平滑连接"""
        try:
            return self.wave_connector.connect_song(song)
        except Exception as e:
            raise Exception(f"平滑连接失败：{e}")

    def _generate_output(self, song):
        """阶段5：输出装配"""
        try:
            return self.output_generator.generate_output(song)
        except Exception as e:
            raise Exception(f"输出装配失败：{e}")


    def get_engine_info(self) -> dict:
        """获取引擎信息"""
        return {
            "version": "Florence Engine v0.5",
            "modules": {
                "decoder": "FlorenceScoreDecoder",
                "synthesizer": "FlorenceSpeakGenerateor",
                "pitch_corrector": "FlorenceCoder",
                "connector": "FlorenceWaveConnecter",
                "renderer": "FlorenceOutputGenerater"
            },
            "sample_rate": self.sample_rate,
            "output_directory": self.output_dir,
            "input_directory": self.input_dir,
            "isDebug":self.isDebug
        }