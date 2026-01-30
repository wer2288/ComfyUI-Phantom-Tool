"""
👻幻影工具 - 任意选择器节点
功能：根据指定索引选择对应输入端口数据输出，含索引/数据合法性校验
支持任意ComfyUI数据类型，前2输入必连、后4输入可选
"""
class AnySelectorNode:
    # 节点分类（固定👻幻影工具）
    CATEGORY = "👻幻影工具"
    # 核心执行函数
    FUNCTION = "select_target_data"
    # 输出端口（*表示任意数据类型，名称固定为输出）
    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("输出",)
    # 允许节点内预览输出结果
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        """定义输入端口：必连+可选+索引选择，严格按需求命名"""
        return {
            "required": {
                # 必连输入：输入任意0、输入任意1（支持任意类型）
                "输入任意0": ("*", {"forceInput": True, "tooltip": "必连 - 任意数据类型"}),
                "输入任意1": ("*", {"forceInput": True, "tooltip": "必连 - 任意数据类型"}),
                # 选择输出索引：默认0，数值输入框
                "选择输出索引": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 5,
                    "step": 1,
                    "display": "number",
                    "tooltip": "选择0-5的索引，对应输出指定输入端口内容"
                })
            },
            "optional": {
                # 可选输入：输入任意2-5（支持任意类型，未连接则为None）
                "输入任意2": ("*", {"tooltip": "可选 - 任意数据类型"}),
                "输入任意3": ("*", {"tooltip": "可选 - 任意数据类型"}),
                "输入任意4": ("*", {"tooltip": "可选 - 任意数据类型"}),
                "输入任意5": ("*", {"tooltip": "可选 - 任意数据类型"})
            }
        }

    def select_target_data(self, 输入任意0, 输入任意1, 选择输出索引, 输入任意2=None, 输入任意3=None, 输入任意4=None, 输入任意5=None):
        """
        核心选择逻辑：
        1. 校验索引范围 2. 映射索引与输入 3. 校验可选输入数据 4. 输出目标数据
        """
        # 校验1：索引是否在0-5范围内，超出则返回错误提示
        if not 0 <= 选择输出索引 <= 5:
            error_msg = "请选择0至5的有效索引数字"
            return (error_msg,)
        
        # 构建索引-输入端口的映射关系，按0-5顺序对应
        input_port_mapping = {
            0: 输入任意0,
            1: 输入任意1,
            2: 输入任意2,
            3: 输入任意3,
            4: 输入任意4,
            5: 输入任意5
        }
        # 获取选中索引对应的输入数据
        target_data = input_port_mapping[选择输出索引]
        
        # 校验2：可选端口（2-5）未连接数据时，返回对应错误提示
        if 选择输出索引 >= 2 and target_data is None:
            error_msg = f"[输入任意{选择输出索引}]无数据输入"
            return (error_msg,)
        
        # 校验通过，输出目标端口数据
        return (target_data,)

# 节点临时注册（最终以__init__.py统一注册为准）
NODE_CLASS_MAPPINGS = {
    "AnySelectorNode": AnySelectorNode
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "AnySelectorNode": "任意选择器"
}