from dataclasses import dataclass


@dataclass
class Context:
    sample_rate:int
    isDebug:bool