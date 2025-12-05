from abc import ABC, abstractmethod  
from FlorenceEngine.Objects.context import Context
import numpy as np

class BaseSpeakGenerator(ABC):
    """
    语音合成生成器的抽象基类
    强制子类实现 generate_song_speech 方法
    """
    context: Context

    def __init__(self, context: Context):
        self.context = context

    @abstractmethod
    def generate_single_word_speech(self, word:str)->np.ndarray:
        """
        抽象方法：必须在子类中实现
        为整个song中的所有word合成原始语音数据
        """
        pass