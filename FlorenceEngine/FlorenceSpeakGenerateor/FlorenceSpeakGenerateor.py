"""
Florence语音合成器 - 使用TTSFactory提供统一的TTS接口
"""
import numpy as np
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

    def __init__(self,context:Context, engine_type: str = ""):
        """
        初始化FlorenceSpeakGenerateor

        Args:
            engine_type: 指定TTS引擎类型('espeak', 'windows', None表示自动选择最佳)
        """
        print("初始化Florence TTS引擎...")

        #接受上下文
        self.context = context
        # 创建TTS工厂
        TSFactory = import_tts_factory()
        if TSFactory is None:
            raise Exception("无法导入TTS工厂，请检查配置")
        self.tts_factory = TSFactory()

        # 根据指定的引擎类型或自动选择最佳引擎
        if engine_type:
            print(f"使用指定TTS引擎: {engine_type}")
            self.tts_engine = self.tts_factory.create_engine(engine_type,self.context)
        else:
            # 自动选择最佳可用引擎
            best_engine_name = self.tts_factory.auto_select_engine()
            print(f"自动选择TTS引擎: {best_engine_name}")
            self.tts_engine = self.tts_factory.create_engine(best_engine_name,self.context)

        # 确保引擎可用
        if self.tts_engine is None:
            raise Exception("无法初始化TTS引擎，请检查系统配置")

        print("TTS引擎初始化成功")


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
            print(f"  合成语音: {word.lrc}")
            word.oriWave = self._generate_single_word_speech(word.lrc)

    def _generate_single_word_speech(self, text: str) -> np.ndarray:
        """
        使用TTS引擎合成语音
        """
        return self.tts_engine.generate_single_word_speech(text)

    def _generate_silence(self, duration: float) -> np.ndarray:
        """生成静音"""
        sample_rate = self.context.sample_rate
        samples = int(sample_rate * duration)
        return np.zeros(samples, dtype=np.float32)

    def get_current_engine_name(self) -> str:
        """获取当前使用的引擎名称"""
        engine = self.get_current_engine()
        return engine.__class__.__name__ if engine else "未知"

    def get_current_engine(self):
        """获取当前使用的引擎"""
        return self.tts_factory.get_current_engine(self.context) if hasattr(self.tts_factory, 'get_current_engine') else self.tts_engine

    def get_available_engines(self) -> list:
        """获取可用引擎列表"""
        return self.tts_factory.get_available_engines()


def main():
    pass


if __name__ == "__main__":
    main()