import numpy as np
from FlorenceEngine.Objects.data_models import Song, Section
from FlorenceEngine.Objects.context import Context

class FlorenceWaveConnecter:
    """
    FlorenceWaveConnecter (重构版)
    职责：基于 Word.start 和 Word.end 时间戳，将离散的音频片段在时域上进行叠加混合 (Overlap-Add)。
    """

    context: Context

    def __init__(self, context: Context):
        self.context = context

    def connect_song(self, song: Song) -> Song:
        """
        处理 Song 中的所有 Track 和 Section
        """
        print("开始基于时间轴组装音频...")
        for track in song.trackList:
            for section in track.sectionList:
                self._connect_section(section)
        
        print("音频组装完成")
        return song

    def _connect_section(self, section: Section) -> None:
        """
        核心逻辑：创建画布，将所有 Word 的波形按时间戳叠加
        """
        if not section.wordList:
            return

        # 1. 确定画布的时间范围
        # Section 的起始时间是第一个词的开始时间
        # Section 的结束时间是最后一个词的结束时间
        base_time = section.wordList[0].time.start
        end_time = section.wordList[-1].time.end
        
        # 计算总持续时间 (秒) + 0.5秒的尾音余量 (防止混响或拖音被截断)
        duration = end_time - base_time + 0.5
        
        # 创建画布 (全零数组)
        total_samples = int(duration * self.context.sample_rate)
        canvas = np.zeros(total_samples, dtype=np.float32)

        # 2. 遍历并叠加音频
        for word in section.wordList:
            # 获取音频源：优先用变调后的 pitchedWave，没有则用 oriWave
            source_wave = word.pitchedWave if word.pitchedWave is not None else word.oriWave
            
            # 如果没有波形数据，跳过
            if source_wave is None or len(source_wave) == 0:
                continue

            # 3. 计算相对位置
            # 该词在画布上的起始采样点 = (该词绝对开始时间 - Section绝对开始时间) * 采样率
            relative_start_time = word.time.start - base_time
            start_idx = int(relative_start_time * self.context.sample_rate)
            end_idx = start_idx + len(source_wave)

            # 4. 动态扩展画布 (如果波形长度超过了预估的 end_time)
            if end_idx > len(canvas):
                padding = np.zeros(end_idx - len(canvas), dtype=np.float32)
                canvas = np.concatenate([canvas, padding])

            # 5. 应用去点击包络 (De-clicking)
            # 给每个片段首尾加极短的淡入淡出，防止叠加处产生爆音
            processed_wave = self._apply_declick_envelope(source_wave)

            # 6. 叠加混音 (Additive Mixing)
            # 使用 += 允许波形自然重叠，无需关心 duration 是否匹配
            canvas[start_idx:end_idx] += processed_wave

        # 7. 赋值结果
        # 注意：这里不做归一化，保留动态范围，由后续混音流程处理
        section.sectionSrc = canvas

    def _apply_declick_envelope(self, wave: np.ndarray) -> np.ndarray:
        """
        应用极短(5ms)的淡入淡出，消除波形切断造成的咔哒声
        """
        fade_samples = int(0.005 * self.context.sample_rate) # 5ms
        
        # 如果波形太短，相应缩短淡化时间
        if len(wave) < fade_samples * 2:
            fade_samples = len(wave) // 2
        
        if fade_samples == 0:
            return wave

        # 必须拷贝，防止修改原引用
        processed = wave.copy()

        # 线性淡入淡出
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)

        processed[:fade_samples] *= fade_in
        processed[-fade_samples:] *= fade_out

        return processed