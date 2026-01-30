from typing import List, Dict, Any

class TextMergeNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "文本1": ("STRING", {
                    "forceInput": True,
                    "label": "文本1"
                }),
                "文本2": ("STRING", {
                    "forceInput": True,
                    "label": "文本2"
                }),
                "合并模式": (["追加模式", "拼接模式", "换行", "空一行"], {
                    "default": "追加模式",
                    "label": "合并模式",
                    "tooltip": "选择文本合并方式：追加模式（逗号分隔）、拼接模式（直接拼接）、换行（单换行）、空一行（双换行）"
                })
            },
            "optional": {
                "文本3": ("STRING", {
                    "label": "文本3",
                    "forceInput": True
                }),
                "文本4": ("STRING", {
                    "label": "文本4",
                    "forceInput": True
                })
            }
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")  # 固定触发刷新

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("合并文本",)
    FUNCTION = "merge_texts"
    CATEGORY = "👻幻影工具"
    OUTPUT_NODE = True  # 支持节点内预览

    def merge_texts(self, 文本1: str, 文本2: str, 合并模式: str = "追加模式", **kwargs) -> tuple:
        try:
            # 收集非空文本（按顺序处理）
            texts: List[str] = []
            
            # 校验必填文本
            if not 文本1.strip():
                return ("错误：文本1不能为空",)
            if not 文本2.strip():
                return ("错误：文本2不能为空",)
            texts.extend([文本1.strip(), 文本2.strip()])
            
            # 收集可选文本（仅处理文本3和文本4）
            for i in range(3, 5):
                text_key = f"文本{i}"
                if text_key in kwargs and kwargs[text_key] and kwargs[text_key].strip():
                    texts.append(kwargs[text_key].strip())

            # 根据合并模式设置分隔符
            separator_map = {
                "追加模式": ",",
                "拼接模式": "",
                "换行": "\n",
                "空一行": "\n\n"
            }
            separator = separator_map.get(合并模式, ",")
            merged_text = separator.join(texts)

            # 生成预览信息（节点内显示）
            preview = (
                f"✅ 合并成功 | 文本数：{len(texts)} | 模式：{合并模式}\n"
                f"📊 总长度：{len(merged_text)}字符\n"
                f"-------------------------\n"
                f"{merged_text[:200]}{'...' if len(merged_text) > 200 else ''}"
            )
            print(preview)  # 输出到节点预览面板

            return (merged_text,)
        except Exception as e:
            return (f"合并失败：{str(e)}",)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "文本合并节点（固定4端口）": TextMergeNode
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "文本合并节点（固定4端口）": "文本合并节点（固定4端口）"
}
