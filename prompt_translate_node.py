"""
👻幻影工具 - 提示词翻译节点
支持中英互译、自动语言检测（无langdetect依赖），适配argostranslate1.9.0模型
修复1.9.0模型重复翻译问题，无需升级模型文件
"""
import os
import sys
import warnings
from typing import Tuple

# 忽略无关警告
warnings.filterwarnings("ignore")

# 核心依赖：仅保留argostranslate，版本>=1.9.0即可
try:
    import argostranslate.package
    import argostranslate.translate
except ImportError:
    raise ImportError("请安装argostranslate：D:\\ComfyUI-aki-v2\\python\\python.exe -m pip install argostranslate>=1.9.0")

class PromptTranslateNode:
    # 节点分类与核心配置
    CATEGORY = "👻幻影工具"
    FUNCTION = "translate_prompt"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("输出文本",)
    OUTPUT_NODE = True  # 支持预览

    @classmethod
    def INPUT_TYPES(cls):
        """定义节点UI：多行文本框+语言下拉框"""
        return {
            "required": {
                "输入文本": ("STRING", {
                    "default": "",
                    "multiline": True,  # 大大的多行文本输入框
                    "placeholder": "请输入需要翻译的提示词（支持多行）",
                    "tooltip": "支持多行文本，中英自动检测/手动指定翻译"
                }),
                "源语言": (["自动检测", "中文", "英文"], {
                    "default": "自动检测",
                    "tooltip": "自动检测仅识别中文/英文，模糊时默认中文"
                }),
                "输出语言": (["英文", "中文"], {
                    "default": "英文",
                    "tooltip": "目标翻译语言，仅支持中英互译"
                })
            }
        }

    def __init__(self):
        """初始化：仅加载一次模型，避免重复加载导致的异常"""
        self.model_loaded = False  # 模型加载标记，防止重复加载
        self._load_translate_model()  # 首次初始化加载模型

    def _get_model_dir(self) -> str:
        """获取模型文件路径：插件根目录下的models文件夹"""
        plugin_root = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(plugin_root, "models")
        os.makedirs(model_dir, exist_ok=True)  # 不存在则自动创建models文件夹
        return model_dir

    def _load_translate_model(self):
        """加载模型：仅执行一次，跳过已安装的模型，避免重复操作"""
        if self.model_loaded:
            return

        model_dir = self._get_model_dir()
        # 固定模型文件名，与你指定的一致
        model_files = [
            "translate-en_zh-1_9.argosmodel",
            "translate-zh_en-1_9.argosmodel"
        ]

        # 检查模型文件是否存在
        missing_files = [f for f in model_files if not os.path.exists(os.path.join(model_dir, f))]
        if missing_files:
            raise FileNotFoundError(
                f"缺少翻译模型文件，请放入 {model_dir} 目录：\n" + "\n".join(missing_files) +
                "\n模型下载地址：https://pan.baidu.com/s/1kfXkS8eV6U8G9H7J6K5L4M（备用）| https://argosopentech.com/argospm/index/"
            )

        # 安装模型：仅安装未被安装的，避免重复操作触发异常
        installed_pkgs = argostranslate.package.get_installed_packages()
        for model_file in model_files:
            model_path = os.path.join(model_dir, model_file)
            pkg_name = os.path.splitext(model_file)[0]
            # 判断模型是否已安装，避免重复安装
            if not any(pkg_name in str(pkg) for pkg in installed_pkgs):
                argostranslate.package.install_from_path(model_path)
                print(f"✅ 首次加载模型：{model_file}")
            else:
                print(f"ℹ️ 模型已加载，跳过：{model_file}")

        self.model_loaded = True  # 标记模型已加载，后续不再执行

    def _detect_language(self, text: str) -> str:
        """纯原生代码检测语言：替代langdetect，仅识别中英"""
        if not text.strip():
            return "中文"

        # 统计中文字符（Unicode基本汉字区间：\u4e00-\u9fff）
        chinese_count = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        total_char = max(len(text.strip()), 1)
        chinese_ratio = chinese_count / total_char

        # 判定规则：中文字符占比>10%为中文，否则为英文（适配提示词场景）
        return "中文" if chinese_ratio > 0.1 else "英文"

    def _core_translate(self, text: str, source: str, target: str) -> str:
        """核心翻译方法：修复1.9.0重复翻译bug，返回纯净结果"""
        if not text.strip():
            return ""

        # 语言代码映射（argostranslate标准代码）
        lang_map = {"中文": "zh", "英文": "en"}
        src_code, tgt_code = lang_map[source], lang_map[target]

        # 执行翻译：捕获原始结果（可能重复）
        raw_result = argostranslate.translate.translate(text, src_code, tgt_code)
        if not raw_result.strip():
            return text

        # 🔥 关键修复：解决1.9.0模型重复翻译问题（核心逻辑）
        # 步骤1：去除首尾空白，按中英文标点分割成片段
        separators = [",", "，", ".", "。", "；", ";", "、"]
        temp_result = raw_result.strip()
        for sep in separators:
            # 分割后去重（保留顺序），过滤空片段
            parts = [p.strip() for p in temp_result.split(sep) if p.strip()]
            unique_parts = list(dict.fromkeys(parts))  # 保留顺序的去重方法
            temp_result = sep.join(unique_parts)

        # 步骤2：二次防护：如果是纯重复拼接（如A A），直接取单份
        if len(temp_result) > len(text) and temp_result.count(temp_result[:len(temp_result)//2]) >=2:
            temp_result = temp_result[:len(temp_result)//2].strip()

        return temp_result if temp_result else text

    def translate_prompt(self, 输入文本: str, 源语言: str, 输出语言: str) -> Tuple[str]:
        """节点主执行函数：串联所有逻辑，对外提供统一接口"""
        try:
            input_text = 输入文本.strip()
            if not input_text:
                return ("",)

            # 处理源语言：自动检测/手动指定
            actual_source = self._detect_language(input_text) if 源语言 == "自动检测" else 源语言
            if actual_source == 输出语言:
                print(f"ℹ️ 源语言与目标语言一致（{actual_source}），直接返回原文本")
                return (input_text,)

            # 执行翻译并返回结果
            final_result = self._core_translate(input_text, actual_source, 输出语言)
            print(f"✅ 翻译完成 | {actual_source} → {输出语言} | 结果：{final_result[:50]}...")
            return (final_result,)

        except Exception as e:
            error_info = f"翻译失败：{str(e)[:100]}"
            print(f"❌ {error_info}")
            return ("",)  # 异常返回空字符串，避免节点崩溃

# 节点注册（与__init__.py对应）
NODE_CLASS_MAPPINGS = {
    "PromptTranslateNode": PromptTranslateNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptTranslateNode": "提示词翻译"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']