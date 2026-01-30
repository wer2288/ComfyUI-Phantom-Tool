import os
from typing import Dict, Any, Union

class MultipleModifierNode:
    """倍数修改器节点：将输入数值转换为最接近的指定倍数，支持多类型输入输出"""
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "输入数值": ("*", {"tooltip": "输入数值（支持整数、浮点、字符串、字符、文本类型）"}),
                "倍数选择": (
                    [8, 16, 32, 64, 128, 256, 512],
                    {"default": 8, "tooltip": "选择目标倍数，输入值会转换为最接近的该倍数"}
                )
            }
        }

    # 输出端口定义
    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("输出数值",)
    FUNCTION = "modify_multiple"
    CATEGORY = "👻幻影工具"
    OUTPUT_NODE = True  # 允许UI直接查看输出

    def _convert_to_numeric(self, value: Any) -> Union[float, None]:
        """通用类型转数值：支持整数、浮点、字符串、字符、文本转换为浮点型"""
        if value is None:
            return None
        
        # 基础数值类型直接返回
        if isinstance(value, (int, float)):
            return float(value)
        
        # 布尔值转换（True=1, False=0）
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        
        # 字符串/字符/文本转换（提取数字部分）
        if isinstance(value, str):
            # 去除空白字符后尝试转换
            cleaned_str = value.strip()
            try:
                return float(cleaned_str)
            except ValueError:
                # 若纯文本无数字，返回0（也可根据需求调整）
                return 0.0
        
        # 列表/元组：取第一个可转换的数值
        if isinstance(value, (list, tuple)):
            for item in value:
                converted = self._convert_to_numeric(item)
                if converted is not None:
                    return converted
            return 0.0
        
        # 其他类型尝试强制转换
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _get_closest_multiple(self, num: float, multiple: int) -> float:
        """计算最接近输入值的指定倍数（修复：小于倍数时返回倍数，否则四舍五入）"""
        if num <= 0:
            return float(multiple)  # 输入0/负数时直接返回最小倍数
        # 计算四舍五入后的倍数
        rounded = round(num / multiple) * multiple
        # 若四舍五入后为0（如num=3, multiple=8），则返回multiple
        return float(rounded) if rounded > 0 else float(multiple)

    def modify_multiple(self, 输入数值: Any, 倍数选择: int = 8) -> tuple[Any]:
        """核心逻辑：转换输入值→计算最接近倍数→保持原输入类型输出"""
        # 1. 转换输入为数值
        numeric_value = self._convert_to_numeric(输入数值)
        if numeric_value is None:
            numeric_value = 0.0
        
        # 2. 计算最接近的指定倍数
        closest_multiple = self._get_closest_multiple(numeric_value, 倍数选择)
        
        # 3. 匹配原输入类型输出（保持类型一致性）
        original_type = type(输入数值)
        try:
            # 处理字符串/字符/文本类型
            if original_type == str:
                output_value = str(int(closest_multiple) if closest_multiple.is_integer() else closest_multiple)
            # 处理整数类型
            elif original_type == int:
                output_value = int(closest_multiple)
            # 处理浮点类型
            elif original_type == float:
                output_value = closest_multiple
            # 其他类型（如bool、list等）转为字符串
            else:
                output_value = str(closest_multiple)
        except:
            # 兜底：转为字符串
            output_value = str(closest_multiple)
        
        return (output_value,)

# 节点映射（临时，最终会合并到__init__.py）
NODE_CLASS_MAPPINGS = {"MultipleModifierNode": MultipleModifierNode}
NODE_DISPLAY_NAME_MAPPINGS = {"MultipleModifierNode": "倍数修改器"}