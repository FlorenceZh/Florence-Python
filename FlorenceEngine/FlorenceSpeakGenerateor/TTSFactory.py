from typing import List, Type, Optional

# 导入基类和上下文定义
from FlorenceEngine.Objects.context import Context
from .InterEngine.base import BaseSpeakGenerator

# 导入具体的引擎实现类
# 注意：这里导入的是类，不是模块
from .InterEngine.HuiHui import WindowsHuiHuiSpeakGenerateor
# 以后可以在这里导入更多，例如: from .InterEngine.Espeak import EspeakGenerator

class TTSFactory:
    """
    TTS 引擎工厂类
    负责管理可用引擎列表，并根据请求实例化具体的引擎
    """
    
    # 核心列表：存储所有可用的引擎“类”（不是实例）
    # 类型注解 List[Type[...]] 表示列表里装的是类本身
    usable_list: List[Type[BaseSpeakGenerator]] = [
        WindowsHuiHuiSpeakGenerateor,
        # EspeakGenerator, # 未来添加
    ]

    def get_available_engines(self) -> List[str]:
        """获取所有可用引擎的名称列表"""
        return [cls.__name__ for cls in self.usable_list]

    def auto_select_engine(self) -> str:
        """
        自动选择最佳引擎（通常是列表中的第一个）
        返回引擎名称
        """
        if not self.usable_list:
            raise Exception("工厂中没有注册任何TTS引擎！")
        
        # 默认返回第一个注册的引擎名称
        # 这里可以加入更复杂的逻辑，比如检测操作系统来决定返回哪个
        return self.usable_list[0].__name__
    
    def get_current_engine(self,context:Context) -> BaseSpeakGenerator:
        """
        自动选择最佳引擎（通常是列表中的第一个）
        返回引擎名称
        """
        if not self.usable_list:
            raise Exception("工厂中没有注册任何TTS引擎！")
        
        # 默认返回第一个注册的引擎名称
        # 这里可以加入更复杂的逻辑，比如检测操作系统来决定返回哪个
        return self.usable_list[0](context)

    def create_engine(self, engine_name: str, context: Context) -> BaseSpeakGenerator:
        """
        根据名称创建并返回引擎实例
        
        Args:
            engine_name: 引擎类名 或 关键词 (如 'windows')
            context: 初始化引擎必须的上下文对象
        """
        target_class = None

        # 1. 尝试精确匹配或模糊匹配
        for cls in self.usable_list:
            # 检查类名是否包含请求的名称 (忽略大小写)
            # 例如: "Windows" 可以匹配 "WindowsHuiHuiSpeakGenerateor"
            if engine_name.lower() in cls.__name__.lower():
                target_class = cls
                break
        
        # 2. 如果没找到，且列表不为空，如果是自动选择模式可能会走到这里
        if target_class is None:
            # 如果指定了名称但没找到，抛出异常
            available = self.get_available_engines()
            raise ValueError(f"未找到名为 '{engine_name}' 的TTS引擎。可用引擎: {available}")

        # 3. 实例化类，并传入 context
        # 这一步是工厂的核心：只有在这里才真正创建对象
        print(f"Factory: 正在实例化 {target_class.__name__}...")
        return target_class(context)