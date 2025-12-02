"""
Florence语音合成器 - 使用TTSFactory提供统一的TTS接口
"""

import numpy as np
from typing import List
from FlorenceEngine.Objects.data_models import Song, Word
from FlorenceEngine.Objects.context import Context

# 动态导入模块，避免循环导入
def import_tts_factory():
    """导入TTS工厂"""
    try:
        from .TTSFactory import TTSFactory
        return TTSFactory
    except ImportError:
        return None


class FlorenceSpeakGenerateor:
    context:Context
    """输入一个song对象，对里面的word对象处理，根据lrc合成oriWave"""

    def __init__(self, engine_type: str = ""):
        """
        初始化FlorenceSpeakGenerateor

        Args:
            engine_type: 指定TTS引擎类型('espeak', 'windows', None表示自动选择最佳)
        """
        print("初始化Florence TTS引擎...")

        #接受上下文

        # 创建TTS工厂
        TSFactory = import_tts_factory()
        if TSFactory is None:
            raise Exception("无法导入TTS工厂，请检查配置")
        self.tts_factory = TSFactory()

        # 根据指定的引擎类型或自动选择最佳引擎
        if engine_type:
            print(f"使用指定TTS引擎: {engine_type}")
            self.tts_engine = self.tts_factory.create_engine(engine_type)
        else:
            # 自动选择最佳可用引擎
            best_engine_name = self.tts_factory.auto_select_engine()
            print(f"自动选择TTS引擎: {best_engine_name}")
            self.tts_engine = self.tts_factory.create_engine(best_engine_name)

        # 确保引擎可用
        if self.tts_engine is None:
            raise Exception("无法初始化TTS引擎，请检查系统配置")

        print("TTS引擎初始化成功")

    @staticmethod
    def judgeChinese(string: str) -> bool:
        """
        如果全是中文，则返回True
        """
        for char in string:
            if '\u4e00' <= char <= '\u9fa5':
                return True
        return False

    def generate_song_speech(self, song: Song) -> Song:
        """
        为整个song中的所有word合成原始语音数据

        Args:
            song: Song对象

        Returns:
            处理后包含oriWave数据的Song对象
        """
        print(f"开始处理歌曲，共{len(song.trackList)}个track")

        for i, track in enumerate(song.trackList):
            print(f"处理第{i+1}个track...")
            for section in track.sectionList:
                self._process_section(section)

        print("所有语音合成完成")
        return song

    def _process_section(self, section):
        """处理整个section中的所有words"""
        for word in section.wordList:
            # 只为还没有oriWave的word生成语音
            if word.oriWave is None:
                print(f"  合成语音: {word.lrc}")
                word.oriWave = self._generate_single_word_speech(word.lrc)

    def _generate_single_word_speech(self, text: str) -> np.ndarray:
        """
        使用TTS引擎合成语音
        """
        if self.tts_engine and hasattr(self.tts_engine, '_generate_single_word_speech'):
            return self.tts_engine._generate_single_word_speech(text)
        else:
            # 备用方案：返回静音
            return self._generate_silence(0.5, self.OUTPUT_SAMPLE_RATE)

    def _generate_silence(self, duration: float, sample_rate: int = 11400) -> np.ndarray:
        """生成静音"""
        if sample_rate is None:
            sample_rate = self.OUTPUT_SAMPLE_RATE
        samples = int(sample_rate * duration)
        return np.zeros(samples, dtype=np.float32)

    def get_current_engine_name(self) -> str:
        """获取当前使用的引擎名称"""
        engine = self.get_current_engine()
        return engine.__class__.__name__ if engine else "未知"

    def get_current_engine(self):
        """获取当前使用的引擎"""
        return self.tts_factory.get_current_engine() if hasattr(self.tts_factory, 'get_current_engine') else self.tts_engine

    def get_available_engines(self) -> list:
        """获取可用引擎列表"""
        return self.tts_factory.get_available_engines()


def main():
    """测试新的统一FlorenceSpeakGenerateor"""
    print("=== FlorenceSpeakGenerateor（TTSFactory版）测试 ===")

    from FlorenceEngine.FlorenceSpeakGenerateor.TTSFactory import TTSFactory

    # 显示可用引擎
    factory = TTSFactory()
    available_engines = factory.get_available_engines()
    print(f"可用引擎: {available_engines}")

    # 创建语音合成器（自动选择最佳引擎）
    try:
        generator = FlorenceSpeakGenerateor()
        current_engine = generator.tts_engine.__class__.__name__
        print(f"当前使用引擎: {current_engine}")

        # 测试语音合成
        test_texts = ["你好", "这是测试", "微软慧慧语音合成"]
        for text in test_texts:
            print(f"\n测试文本: {text}")
            audio_data = generator._generate_single_word_speech(text)
            if audio_data is not None:
                print(f"合成成功！音频长度: {len(audio_data)} 样本 ({len(audio_data)/generator.OUTPUT_SAMPLE_RATE:.3f} 秒)")

                # 播放测试
                try:
                    from debugger import play
                    print("正在播放...")
                    play(audio_data, volume=0.7)
                    print("播放完成")
                except Exception as e:
                    print(f"播放失败: {e}")

        print("\n=== 所有测试完成 ===")

    except Exception as e:
        print(f"测试失败: {e}")
        print("请检查TTS引擎配置")


if __name__ == "__main__":
    # 添加项目路径到系统路径
    import sys
    sys.path.append(sys.path[0] if sys.path else '.')
    main()