# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Florence引擎是一个Python实现的乐谱处理和语音合成系统，主要功能是将MusicXML格式的乐谱文件转换为语音输出。

## 核心架构

### 主要模块

1. **FlorenceScoreDecoder** (`FlorenceEngine/FlorenceScoreDecoder/`)
   - `ScoreDecoder`: 解析MusicXML文件，提取音符、歌词和时间信息
   - 音域限制：只处理130Hz(C3)以上的音符
   - 输出Word对象列表用于后续处理

2. **FlorenceSpeakGenerateor** (`FlorenceEngine/FlorenceSpeakGenerateor/`)
   - `TTS`: 使用eSpeak-NG进行文本到语音合成
   - 支持中文到拼音的转换
   - 生成WAV格式的语音数据

3. **Objects** (`FlorenceEngine/Objects/`)
   - `Word`: 包含时间戳、基础频率和歌词的数据结构
   - `Selector`: 提供文件选择对话框UI

## 开发命令

### 依赖安装
```bash
pip install -r requirements.txt
```

### 代码检查
```bash
# 语法检查
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# 类型检查
mypy .
```

### 运行项目
```bash
# 主程序运行
python main.py

# TTS测试
python test.py
```

## 重要依赖

- **music21**: 乐谱解析和处理
- **eSpeak-NG**: 语音合成（需要系统安装）
- **xpinyin**: 中文转拼音

## 文件格式

项目处理`.musicxml`和`.mxl`格式的乐谱文件，要求每个音符都必须包含歌词信息。

## 系统要求

- Windows系统（基于项目中的配置）
- Python 3.13+
- eSpeak-NG需要单独安装并配置PATH环境变量