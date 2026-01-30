import os
from typing import Dict, Any, Union
import math

class NumericCalculatorNode:
    """数值计算器节点：支持多类型输入/自定义公式双模式，输出整数和浮点结果"""
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        inputs = {
            "required": {
                "输出值选择": (  # 原optional中的输出值选择移到required首位
                    ["最大值", "最小值", "求和", "平均值"],
                    {"default": "最大值", "tooltip": "使用计算公式关闭时，选择预设计算方式"}
                ),
            },
            "optional": {
                # 把a/b/c移到optional中，改为可选连接输入，保留原有配置
                "a": ("*", {"tooltip": "输入值a（支持任意类型，自动转换为数值）"}),
                "b": ("*", {"tooltip": "输入值b（支持任意类型，自动转换为数值）"}),
                "c": ("*", {"tooltip": "输入值c（支持任意类型，自动转换为数值）"}),
                # 原required中的使用计算公式移到optional中
                "使用计算公式": ("BOOLEAN", {"default": False, "tooltip": "开启后使用自定义计算公式，关闭则使用预设计算方式"}),
                "计算公式": (
                    "STRING",
                    {"default": "", "tooltip": "使用计算公式开启时，输入自定义表达式（支持a、b、c变量，如(a+b)/c）"}
                )
            }
        }
        return inputs

    # 输出端口定义
    RETURN_TYPES = ("*", "*")
    RETURN_NAMES = ("整数", "浮点")
    FUNCTION = "calculate"
    CATEGORY = "👻幻影工具"
    OUTPUT_NODE = True  # 允许UI直接查看输出

    def _convert_to_numeric(self, value: Any) -> Union[float, int, None]:
        """通用类型转数值：支持各种ComfyUI常见类型转换"""
        if value is None:
            return None
        
        # 基础数值类型直接返回
        if isinstance(value, (int, float)):
            return value
        
        # 布尔值转换（True=1, False=0）
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        
        # 字符串转换（支持数字字符串，如"123", "3.14"）
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None
        
        # 图像类（假设是ComfyUI常见的图像格式，取尺寸相关数值）
        if hasattr(value, "shape"):
            try:
                # 取图像宽度（假设shape为[H, W, C]或[H, W]）
                return float(value.shape[1])
            except (IndexError, AttributeError):
                return None
        
        # 列表/元组：取第一个可转换的数值
        if isinstance(value, (list, tuple)):
            for item in value:
                converted = self._convert_to_numeric(item)
                if converted is not None:
                    return converted
            return None
        
        # 字典：尝试提取常见数值字段
        if isinstance(value, dict):
            for key in ["width", "height", "value", "num", "size"]:
                if key in value:
                    converted = self._convert_to_numeric(value[key])
                    if converted is not None:
                        return converted
            return None
        
        # 其他类型尝试强制转换
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _round_float_precision(self, value: float, decimals: int = 10) -> float:
        """修正浮点精度问题：四舍五入到指定小数位，解决0.1+0.2=0.30000000000000004这类问题"""
        return round(value * 10**decimals) / 10**decimals

    def calculate(self, 输出值选择: str = "最大值", 使用计算公式: bool = False, a: Any = None, b: Any = None, c: Any = None, 计算公式: str = "") -> tuple[int, float]:
        """核心计算逻辑：分预设模式和自定义公式模式，支持多类型输入+浮点精度修正"""
        # 转换所有输入为数值（None不影响，_convert_to_numeric会处理）
        converted_a = self._convert_to_numeric(a)
        converted_b = self._convert_to_numeric(b)
        converted_c = self._convert_to_numeric(c)
        
        # 收集有效数值（过滤转换失败的None）
        valid_nums = [num for num in [converted_a, converted_b, converted_c] if num is not None]
        final_float = 0.0

        # 模式1：关闭自定义公式，使用预设计算方式
        if not 使用计算公式:
            if valid_nums:  # 有有效数值时计算
                if 输出值选择 == "最大值":
                    final_float = max(valid_nums)
                elif 输出值选择 == "最小值":
                    final_float = min(valid_nums)
                elif 输出值选择 == "求和":
                    final_float = sum(valid_nums)
                elif 输出值选择 == "平均值":
                    final_float = sum(valid_nums) / len(valid_nums)
        
        # 模式2：开启自定义公式，执行自定义表达式
        else:
            if 计算公式.strip():  # 公式非空时执行
                try:
                    # 构建变量字典（转换失败/未连接则设为0）
                    var_dict = {
                        "a": converted_a if converted_a is not None else 0.0,
                        "b": converted_b if converted_b is not None else 0.0,
                        "c": converted_c if converted_c is not None else 0.0
                    }
                    # 使用eval执行表达式（仅用于可控场景）
                    raw_result = eval(计算公式, {"__builtins__": None}, var_dict)
                    final_float = float(raw_result)
                except Exception as e:
                    # 公式执行出错时返回0，并打印错误信息
                    print(f"计算公式执行错误: {e}")
                    final_float = 0.0

        # 修正浮点精度问题
        final_float = self._round_float_precision(final_float)
        
        # 计算整数结果（四舍五入）
        final_int = round(final_float)
        
        return (final_int, final_float)

# 节点注册
NODE_CLASS_MAPPINGS = {"NumericCalculatorNode": NumericCalculatorNode}
NODE_DISPLAY_NAME_MAPPINGS = {"NumericCalculatorNode": "数值计算器"}