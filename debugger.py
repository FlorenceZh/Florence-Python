"""
Florence引擎调试工具
用于播放音频数据以进行调试
"""

import numpy as np
import sounddevice as sd
import warnings

class AudioDebugger:
    def __init__(self, sample_rate=22050):
        """
        初始化音频调试器

        Args:
            sample_rate: 采样率，默认为44100Hz
        """
        self.sample_rate = sample_rate
        self.is_playing = False

    def play(self, audio_data, normalize=True, volume=1.0):
        """
        播放numpy数组音频数据

        Args:
            audio_data: numpy数组格式的音频数据
            normalize: 是否归一化音频数据到[-1, 1]范围
            volume: 音量控制（0.0-1.0）

        Returns:
            bool: 播放是否成功
        """
        try:
            # 确保数据是float32类型
            if isinstance(audio_data, np.ndarray):
                audio_copy = audio_data.astype(np.float32)
            else:
                print("错误：输入必须是numpy数组")
                return False

            # 归一化处理
            if normalize:
                max_val = np.max(np.abs(audio_copy))
                if max_val > 0:
                    audio_copy = audio_copy / max_val
                else:
                    print("警告：音频数据全为零")
                    return False

            # 应用音量控制
            audio_copy = audio_copy * volume

            # 确保数据在有效范围内
            audio_copy = np.clip(audio_copy, -1.0, 1.0)

            print(f"正在播放音频数据：长度={len(audio_copy)}, 采样率={self.sample_rate}, 音量={volume}")

            # 播放音频
            self.is_playing = True
            sd.play(audio_copy, self.sample_rate)
            sd.wait()  # 等待播放完成
            self.is_playing = False

            print("音频播放完成")
            return True

        except Exception as e:
            print(f"播放音频时发生错误: {e}")
            return False

    def play_stereo(self, left_channel, right_channel, normalize=True, volume=1.0):
        """
        播放立体声音频（双声道）

        Args:
            left_channel: 左声道数据
            right_channel: 右声道数据
            normalize: 是否归一化
            volume: 音量控制
        """
        try:
            # 确保两个声道长度相同
            min_length = min(len(left_channel), len(right_channel))
            left_channel = left_channel[:min_length]
            right_channel = right_channel[:min_length]

            # 组合成立体声
            stereo_data = np.column_stack([left_channel, right_channel])

            print(f"正在播放立体声音频：长度={min_length}, 采样率={self.sample_rate}")
            self.play(stereo_data, normalize, volume)

        except Exception as e:
            print(f"播放立体声音频时发生错误: {e}")
            return False

    def stop(self):
        """停止播放"""
        if self.is_playing:
            sd.stop()
            self.is_playing = False
            print("播放已停止")

    def save(self, audio_data, filename="temp.wav", normalize=True):
        """
        保存音频数据到WAV文件
        
        Args:
            audio_data: numpy数组
            filename: 文件名或路径
            normalize: 是否归一化到最大音量
        """
        try:
            import scipy.io.wavfile
            import os

            # 确保数据是numpy数组
            if not isinstance(audio_data, np.ndarray):
                print("错误：输入必须是numpy数组")
                return False

            # 转换为float32进行处理
            audio_copy = audio_data.astype(np.float32)

            # 归一化
            if normalize:
                max_val = np.max(np.abs(audio_copy))
                if max_val > 0:
                    audio_copy = audio_copy / max_val
            
            # 确保范围在 [-1, 1]
            audio_copy = np.clip(audio_copy, -1.0, 1.0)

            # 转换为 16-bit PCM (标准wav格式，兼容性最好)
            # 将 float[-1,1] 映射到 int16[-32767, 32767]
            audio_int16 = (audio_copy * 32767).astype(np.int16)

            # 获取绝对路径以便在控制台显示
            full_path = os.path.abspath(filename)

            # 写入文件
            scipy.io.wavfile.write(full_path, self.sample_rate, audio_int16)
            
            print(f"音频已保存至: {full_path}")
            return True

        except ImportError:
            print("保存失败：需要 scipy 库 (请运行 pip install scipy)")
            return False
        except Exception as e:
            print(f"保存文件时出错: {e}")
            return False

    def get_audio_info(self, audio_data):
        """
        获取音频数据信息

        Args:
            audio_data: numpy数组音频数据

        Returns:
            dict: 音频信息
        """
        info = {
            'shape': audio_data.shape,
            'dtype': str(audio_data.dtype),
            'min': np.min(audio_data),
            'max': np.max(audio_data),
            'mean': np.mean(audio_data),
            'length': len(audio_data) if hasattr(audio_data, '__len__') else len(audio_data.flatten()),
            'duration': len(audio_data) / self.sample_rate if hasattr(audio_data, '__len__') else None
        }
        return info

    def print_audio_info(self, audio_data, name="音频数据"):
        """打印音频数据信息"""
        info = self.get_audio_info(audio_data)
        print(f"\n{name} 信息:")
        print(f"  形状: {info['shape']}")
        print(f"  数据类型: {info['dtype']}")
        print(f"  最小值: {info['min']:.6f}")
        print(f"  最大值: {info['max']:.6f}")
        print(f"  平均值: {info['mean']:.6f}")
        print(f"  长度: {info['length']} 样本")
        if info['duration']:
            print(f"  时长: {info['duration']:.3f} 秒")


# 创建全局调试器实例
debugger = AudioDebugger()

# 简化的播放函数，方便在调试控制台中直接使用
def play(audio_data, normalize=True, volume=1.0):
    """
    直接播放numpy数组音频数据

    Args:
        audio_data: numpy数组格式的音频数据
        normalize: 是否归一化音频数据
        volume: 音量控制（0.0-1.0）

    示例:
        import numpy as np
        # 生成1秒的440Hz正弦波
        t = np.linspace(0, 1, 44100)
        sine_wave = np.sin(2 * np.pi * 440 * t)
        play(sine_wave)
    """
    return debugger.play(audio_data, normalize, volume)


def play_stereo(left, right, normalize=True, volume=1.0):
    """
    播放立体声音频

    Args:
        left: 左声道数据
        right: 右声道数据
        normalize: 是否归一化
        volume: 音量控制
    """
    return debugger.play_stereo(left, right, normalize, volume)


def audio_info(audio_data, name="音频数据"):
    """打印音频数据信息"""
    debugger.print_audio_info(audio_data, name)


def stop():
    """停止播放"""
    debugger.stop()


# 测试函数
def test_play():
    """测试播放功能"""
    print("开始测试播放功能...")

    # 生成测试音频数据
    import numpy as np

    # 生成1秒的440Hz正弦波
    duration = 1.0  # 秒
    sample_rate = debugger.sample_rate
    t = np.linspace(0, duration, int(sample_rate * duration))

    # 440Hz A音符
    sine_wave = np.sin(2 * np.pi * 440 * t)

    print("正在播放440Hz测试音频...")
    play(sine_wave)

    # 立体声测试
    print("\n正在测试立体声播放...")
    left = np.sin(2 * np.pi * 440 * t)  # 左声道440Hz
    right = np.sin(2 * np.pi * 880 * t)  # 右声道880Hz（高八度）
    play_stereo(left, right, volume=0.7)

    print("测试完成！")

def save(audio_data, filename="temp.wav", normalize=True):
    """
    保存音频数据到WAV文件 (调试用)
    
    Args:
        audio_data: numpy数组
        filename: 保存路径，默认为 temp.wav
        normalize: 是否自动归一化
    """
    return debugger.save(audio_data, filename, normalize)


if __name__ == "__main__":
    print("Florence引擎音频调试器")
    print("可用的函数:")
    print("  play(audio_data, normalize=True, volume=1.0) - 播放音频数据")
    print("  play_stereo(left, right, normalize=True, volume=1.0) - 播放立体声")
    print("  audio_info(audio_data, name=\"音频数据\") - 打印音频信息")
    print("  stop() - 停止播放")
    print("  test_play() - 运行测试")
    print("\n示例用法:")
    print("  import numpy as np")
    print("  t = np.linspace(0, 1, 44100)")
    print("  sine_wave = np.sin(2 * np.pi * 440 * t)")
    print("  play(sine_wave)")

    # 运行测试
    test_play()