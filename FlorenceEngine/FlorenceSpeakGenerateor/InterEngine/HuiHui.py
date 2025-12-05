"""
基于Windows SAPI和pyttsx3的语音合成器
使用微软Windows内置的语音引擎（包括慧慧）
"""

import numpy as np
import wave
import io
import pyttsx3
import tempfile
import os

from FlorenceEngine.Objects.context import Context
from .base import BaseSpeakGenerator


class WindowsHuiHuiSpeakGenerateor(BaseSpeakGenerator):
    """基于Windows SAPI的语音合成器，使用pyttsx3库"""

    # 上下文
    context:Context 
    engine:pyttsx3.Engine
    chinese_voice_id: str

    def __init__(self,context:Context):
        """
        初始化Windows语音合成引擎
        """
        self.context = context
        self.engine = pyttsx3.init('sapi5')
        self.engine.setProperty('rate', 140)   # 语速，中文建议140左右
        self.engine.setProperty('volume', 0.9) # 音量0.0-1.0

        # 获取并设置中文语音
        voices = self.engine.getProperty('voices')
        huihui_voice = None

        for i, voice in enumerate(voices):
            # 查找语音
            if 'Hui' in voice.name or 'Xiaoxiao' in voice.name:  # 慧慧或晓晓
                huihui_voice = voice
                print(f"找到慧慧/晓晓语音: {voice.id}")
                break

        if huihui_voice:
            self.engine.setProperty('voice', huihui_voice.id)
            self.chinese_voice_id = huihui_voice.id
        else:
            raise Exception("没有找到HuiHui/XiaoXiao的语音")
 
    def generate_single_word_speech(self, word:str) -> np.ndarray:
        """
        使用Windows TTS合成单个词语的语音
        """

        # 创建一个临时WAV文件
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.wav', delete=False) as f:
            temp_wav_path = f.name

        # 保存语音到文件
        self.engine.save_to_file(word, temp_wav_path)
        self.engine.runAndWait()

        # 等待文件写入完成
        attempts = 0
        while not os.path.exists(temp_wav_path) and attempts < 50:
            import time
            time.sleep(0.1)
            attempts += 1

        if not os.path.exists(temp_wav_path):
            raise Exception("语音文件生成失败")

        # 读取生成的WAV文件
        with open(temp_wav_path, 'rb') as f:
            wav_data = f.read()

        # 将WAV数据转换为numpy数组
        audio_data = self._wav_bytes_to_numpy(wav_data)

        # 清理临时文件
        try:
            os.remove(temp_wav_path)
        except:
            pass

        return audio_data

    def _wav_bytes_to_numpy(self, wav_bytes: bytes) -> np.ndarray:
        """
        将WAV字节数据转换为numpy数组
        """

        # 使用wave模块解析WAV数据
        wav_file = wave.open(io.BytesIO(wav_bytes), 'rb')

        # 获取音频参数
        n_channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        sample_rate = wav_file.getframerate()
        n_frames = wav_file.getnframes()

        print(f"WAV参数: {n_channels}声道, {sample_width}字节, {sample_rate}Hz, {n_frames}帧")

        # 读取所有帧
        frames = wav_file.readframes(n_frames)
        wav_file.close()

        # 转换为numpy数组
        if sample_width == 2:  # 16-bit PCM
            audio_data = np.frombuffer(frames, dtype=np.int16)
            # 归一化到[-1, 1]
            audio_data = audio_data.astype(np.float32) / 32768.0
        elif sample_width == 1:  # 8-bit PCM
            audio_data = np.frombuffer(frames, dtype=np.uint8)
            # 归一化到[-1, 1]
            audio_data = (audio_data.astype(np.float32) - 128) / 128.0
        else:
            raise ValueError(f"不支持的采样宽度: {sample_width}")

        # 如果是立体声，转换为单声道
        if n_channels == 2:
            audio_data = audio_data.reshape(-1, 2).mean(axis=1)

        # 如果采样率不是目标采样率，进行重采样
        if sample_rate != self.context.sample_rate:
            audio_data = self._resample_audio(audio_data, sample_rate, self.context.sample_rate)

        return audio_data

    def _resample_audio(self, audio_data: np.ndarray, original_rate: int, target_rate: int) -> np.ndarray:
        """
        简单的音频重采样
        """
        if original_rate == target_rate:
            return audio_data

        # 计算新的长度
        new_length = int(len(audio_data) * target_rate / original_rate)

        # 使用线性插值进行重采样
        old_indices = np.arange(len(audio_data))
        new_indices = np.linspace(0, len(audio_data) - 1, new_length)

        # 线性插值
        resampled_audio = np.interp(new_indices, old_indices, audio_data)

        return resampled_audio.astype(np.float32)

    def _generate_silence(self, duration: float) -> np.ndarray:
        """生成静音"""
        sample_rate = self.context.sample_rate
        samples = int(sample_rate * duration)
        return np.zeros(samples, dtype=np.float32)


# 测试函数
def test_windows_tts():
    """测试Windows TTS功能"""
    print("开始测试Windows TTS语音合成器...")

    try:
        # 创建TTS引擎
        tts = WindowsHuiHuiSpeakGenerateor(Context(44100,True))

        # 测试文本
        test_texts = [
            "你好",
            "这是一段测试语音",
            "微软慧慧语音合成测试"
        ]

        for text in test_texts:
            print(f"\n正在合成: {text}")
            audio_data = tts.generate_single_word_speech(text)

            print(f"音频长度: {len(audio_data)} 样本")
            print(f"预计时长: {len(audio_data)/tts.context.sample_rate:.3f} 秒")

            # 播放测试
            try:
                from debugger import play,save
                print("正在播放...")
                play(audio_data, volume=0.7)
                save(audio_data)
                print("播放完成")
            except Exception as e:
                print(f"播放失败: {e}")

        print("\nWindows TTS测试完成")

    except Exception as e:
        print(f"Windows TTS测试失败: {e}")


if __name__ == "__main__":
    test_windows_tts()