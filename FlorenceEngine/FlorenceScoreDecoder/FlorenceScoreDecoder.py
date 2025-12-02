import os
import re
from typing import List, Optional

from music21 import converter,tempo
from music21.stream import Score, Part, Opus
from music21.stream.iterator import StreamIterator
from music21.note import Note
from xpinyin import Pinyin
from lolviz import objviz

from FlorenceEngine.Objects.data_models import Song, Track, Section, Word, Time
from FlorenceEngine.Objects.context import Context


class FlorenceScoreDecoder:
    """负责处理 MusicXML 输入并解析为 Song 对象"""
    
    # 时间比较的容差值，用于处理浮点数精度问题
    TIME_TOLERANCE = 1e-12
    
    context: Context

    def __init__(self, context: Context):
        self.pinyin_converter = Pinyin()
        self.context = context


    def _normalize_to_score(self, parsed_obj) -> Score:
        """将解析结果统一转换为 Score 对象"""
        if isinstance(parsed_obj, Score):
            return parsed_obj
        elif isinstance(parsed_obj, Part):
            score = Score()
            score.append(parsed_obj)
            return score
        elif isinstance(parsed_obj, Opus):
            return parsed_obj.scores[0] if parsed_obj.scores else Score()
        else:
            raise ValueError(f"解析 MusicXML 失败，非法类型: {type(parsed_obj)}")


    def decode_score(self, score_path: str) -> Song:
        """
        解析 MusicXML 文件并创建 Song 对象
        Args:
            score_path: MusicXML 文件路径
        Returns:
            Song 对象
        """
        parsed = converter.parse(score_path)
        score = self._normalize_to_score(parsed)
        
        # 获取文件名（不含扩展名）
        song_name = os.path.splitext(os.path.basename(score_path))[0]

        song = Song(
            trackList=[],
            name=song_name
        )
        #统一补全速度标记
        self._set_part_tempo(parts=score.parts)

        # 处理每个声部
        for part in score.parts:
            try:
                track = self._process_part(part)
                song.trackList.append(track)
            except Exception as e:
                # 这里可以选择捕获单个声部的错误，以免整个文件解析失败
                # 或者直接抛出，取决于业务需求。这里保留抛出。
                raise RuntimeError(f"处理声部 {part.id} 时出错: {str(e)}") from e

        if self.context.isDebug:
            obj = objviz(song)
            obj.view()

        return song
    
    def _set_part_tempo(self,parts:StreamIterator[Part])->None:
        """
        操作的是引用，不用返回
        """
        #默认第一轨速度
        target_part = parts[0]

        for part in parts[1:]:
            #检查是否已有速度标记
            part_tempos = part.flatten().getElementsByClass(tempo.MetronomeMark)
            #若有则不加
            if not part_tempos:
                self._set_tempo(target_part,part)

    
    def _set_tempo(self,target_part:Part,to_insrt_part:Part)->Part:
        tempos = target_part.flatten().getElementsByClass(tempo.MetronomeMark)
        for mm in tempos:
            # mm.offset 是它在乐谱中的绝对位置
            to_insrt_part.insert(mm.offset, mm)
        return to_insrt_part

    def _process_part(self, part) -> Track:
        """
        主流程：处理单个声部
        1. 提取所有有效的 Word 对象
        2. 将 Word 对象按时间分组成 Section
        3. 组装成 Track
        """
        # 第一步：数据清洗与转换 (music21 -> List[Word])
        words = self._extract_words(part)
        
        if not words:
            # 如果一个声部完全没有歌词或音符，可以根据需求返回空 Track 或抛出异常
            # 这里根据原逻辑抛出异常
            raise ValueError("该声部未提取到有效的歌词/音符数据。")

        # 第二步：逻辑分段 (List[Word] -> List[Section])
        sections = self._group_words_to_sections(words)

        # 第三步：组装
        return Track(sectionList=sections)

    def _extract_words(self, part) -> List[Word]:
        """从 music21 part 中提取并转换为 Word 对象列表"""
        words: List[Word] = []
        
        # 使用 secondsMap 获取绝对秒数时间
        for event in part.flatten().secondsMap:
            element = event['element']
            
            # 1. 过滤非音符元素 (Guard Clause)
            # 原代码中的 pass 是错误的，会导致后续 element.lyric 报错
            if not isinstance(element, Note):
                continue
                
            # 2. 校验歌词
            if not element.lyric:
                raise ValueError(f"音符缺少歌词：位置 {element.offset}, 音高 {element.pitch}")

            # 3. 创建 Word 对象
            word = self._create_word_from_event(event, element)
            words.append(word)
            
            # Debug 输出
            if self.context.isDebug:
                print(f"{str(element.pitch):<10} | {element.offset:<15} | "
                      f"{word.time.start:<15.4f} | {word.time.end:<15.4f}|{word.lrc:<5}")
                      
        return words

    def _create_word_from_event(self, event, element) -> Word:
        """工厂方法：根据 music21 事件创建 Word 对象"""
        start_seconds = event['offsetSeconds']
        duration_seconds = event['durationSeconds']
        
        return Word(
            pitch=element.pitch.frequency,
            time=Time(start=start_seconds, end=start_seconds + duration_seconds),
            lrc=self._convert_to_pinyin(element.lyric)
        )

    def _group_words_to_sections(self, words: List[Word]) -> List[Section]:
        """核心算法：根据时间连续性将 Word 聚类为 Section"""
        sections: List[Section] = []
        if not words:
            return sections

        current_batch: List[Word] = [words[0]]
        
        # 从第二个词开始遍历，与前一个词比较
        for current_word in words[1:]:
            previous_word = current_batch[-1]
            
            # 判断是否断开：当前开始时间 - 上一个结束时间 > 容差
            # 如果 gap 很小（接近0或负数即重叠），则视为连续
            time_gap = current_word.time.start - previous_word.time.end
            
            if time_gap > self.TIME_TOLERANCE:
                # 发现断点：封装旧段落
                sections.append(self._create_validated_section(current_batch))
                # 开启新段落
                current_batch = []
            
            current_batch.append(current_word)

        # 处理剩余的最后一个段落
        if current_batch:
            sections.append(self._create_validated_section(current_batch))
            
        return sections
    
    def _normalnize_time(self,wordList:List[Word])->List[Word]:
        # zip 会自动停止在较短的那个列表结束处，所以不会越界
        for current_word, next_word in zip(wordList, wordList[1:]):
            # 核心逻辑：当前结束 = 下一个开始
            current_word.time.end = next_word.time.start
            
        return wordList


    def _create_validated_section(self, word_list: List[Word]) -> Section:
        """创建 Section 对象并执行重叠检查"""
        # 确保每个段落都被检查
        self._check_overlap(word_list)
        
        normalized_word_list = self._normalnize_time(word_list)
        
        return Section(
            wordList=normalized_word_list,
            sectionStart=word_list[0].time.start
        )

    def _convert_to_pinyin(self, text: str) -> str: 
        """转换中文为拼音并去除声调"""
        if not text:
            return ""
            
        # 如果是纯英文字符，直接返回
        if text.isascii():
            return text.lower()

        # 转换为拼音 (tone_marks='numbers' 生成如 "ni3")
        pinyin = self.pinyin_converter.get_pinyin(text, tone_marks='numbers')

        # 去除声调数字
        pinyin_no_tone = re.sub(r'\d', '', pinyin)

        return pinyin_no_tone.lower()

    def _check_overlap(self, words: List[Word]) -> None:
        """检查音符列表中是否存在非法的时间重叠"""
        if len(words) < 2:
            return

        for i in range(len(words) - 1):
            current_word = words[i]
            next_word = words[i + 1]

            # 如果 (当前结束 - 下一个开始) > 容差，说明重叠了
            # 例如：当前在 5s 结束，下一个在 4s 开始，差值 1s > 1e-12，报错
            overlap = current_word.time.end - next_word.time.start
            
            if overlap > self.TIME_TOLERANCE:
                raise ValueError(
                    f"音符时间重叠：第{i}个音符结束时间({current_word.time.end:.4f}) "
                    f"> 第{i+1}个音符开始时间({next_word.time.start:.4f})"
                )