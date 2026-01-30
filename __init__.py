from .txt_loader_node import TXTLoaderNode
from .text_merge_node import TextMergeNode
from .numeric_calculator_node import NumericCalculatorNode
from .multiple_modifier_node import MultipleModifierNode
from .any_selector_node import AnySelectorNode
from .video_frame_extract_node import VideoFrameExtractNode

NODE_CLASS_MAPPINGS = {
    "TXTLoaderNode": TXTLoaderNode,
    "TextMergeNode": TextMergeNode,
    "NumericCalculatorNode": NumericCalculatorNode,
    "MultipleModifierNode": MultipleModifierNode,
    "AnySelectorNode": AnySelectorNode,
    "VideoFrameExtractNode": VideoFrameExtractNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TXTLoaderNode": "TXT文件批量加载",
    "TextMergeNode": "文本合并",
    "NumericCalculatorNode": "数值计算器",
    "MultipleModifierNode": "倍数修改器",
    "AnySelectorNode": "任意选择器",
    "VideoFrameExtractNode": "视频首尾帧获取"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
