import numpy as np
import pyworld as pw
from FlorenceEngine.Objects.data_models import Song, Word, Section
from FlorenceEngine.Objects.context import Context

class FlorenceCoder:
    """
    FlorenceCoder (World声码器封装)
    职责：单一职责，仅负责读取Word中的oriWave，根据Word.pitch进行变调，并将结果写入Word.pitchedWave
    """

    context: Context
    frame_period: float

    def __init__(self, context: Context, frame_period: float = 5.0):
        """
        Args:
            context: 上下文对象，包含采样率等信息
            frame_period: World分析的帧周期（毫秒），默认5.0ms
        """
        self.context = context
        self.frame_period = frame_period

    def process_song(self, song: Song) -> Song:
        """
        遍历Song中的所有Word，执行音高校正
        """
        print("开始进行声码器音高处理...")
        for track in song.trackList:
            for section in track.sectionList:
                for word in section.wordList:
                    self._process_word(word)
        
        print("音高处理完成")
        return song

    def _process_word(self, word: Word) -> None:
        """
        处理单个Word的音高
        """
        # 基础检查：必须有原始音频且有目标音高
        if word.oriWave is None or len(word.oriWave) == 0:
            return
        
        if word.pitch is None or word.pitch <= 0:
            # 如果没有指定音高，视情况可以直接复制原始音频，或者保持为None
            # 这里选择简单的跳过，或者你可以选择: word.pitchedWave = word.oriWave.copy()
            return

        try:
            # 执行变调核心逻辑
            word.pitchedWave = self._shift_pitch(word.oriWave, word.pitch)
        except Exception as e:
            print(f"处理单词 '{word.lrc}' 变调时出错: {e}")
            # 出错时回退策略：使用原始音频
            word.pitchedWave = word.oriWave.copy()

    def _shift_pitch(self, audio: np.ndarray, target_freq: float) -> np.ndarray:
        """
        使用PyWorld进行变调的核心算法
        
        Args:
            audio: 原始音频数据 (float32)
            target_freq: 目标频率 (Hz)
            
        Returns:
            变调后的音频数据 (float32)
        """
        sample_rate = self.context.sample_rate

        # 1. 类型转换：PyWorld 需要 float64
        x = audio.astype(np.float64)

        # 2. DIO 算法提取基频 (F0)
        f0, t = pw.dio(x, sample_rate, frame_period=self.frame_period)

        # 3. StoneMask 修正基频
        f0 = pw.stonemask(x, f0, t, sample_rate)

        # 4. CheapTrick 提取频谱包络 (Spectral Envelope)
        sp = pw.cheaptrick(x, f0, t, sample_rate)

        # 5. D4C 提取非周期性指数 (Aperiodicity)
        ap = pw.d4c(x, f0, t, sample_rate)

        # 6. 计算音高偏移量
        # 过滤掉无声部分(f0=0)来计算平均基频
        valid_f0 = f0[f0 > 0]
        
        if len(valid_f0) == 0:
            # 如果整段音频都没有检测到基频（全是清音或静音），直接返回原音频
            return audio.copy()

        current_avg_f0 = np.mean(valid_f0)
        pitch_ratio = target_freq / current_avg_f0

        # 7. 修改基频
        # 保持原本的抑扬顿挫（轮廓），整体平移到目标音高
        modified_f0 = f0 * pitch_ratio

        # 安全限制：防止频率超出World的处理范围导致崩溃 (通常限制在 50Hz - 1000Hz 之间比较安全)
        # 注意：这里只限制有声部分，0仍然保持0
        modified_f0 = np.where(modified_f0 > 0, np.clip(modified_f0, 50, 1600), 0)

        # 8. 合成新音频
        y = pw.synthesize(modified_f0, sp, ap, sample_rate, frame_period=self.frame_period)

        # 9. 长度对齐
        # 合成后的长度可能与原长度有细微差异，强制对齐以免后续拼接出问题
        if len(y) != len(audio):
            if len(y) > len(audio):
                y = y[:len(audio)]
            else:
                y = np.pad(y, (0, len(audio) - len(y)), mode='constant')

        return y.astype(np.float32)