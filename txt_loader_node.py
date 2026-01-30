import os
import glob

class TXTLoaderNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "文件路径": ("STRING", {  # 参数名改为中文
                    "default": "",
                    "multiline": False,
                    "placeholder": "请输入TXT文件所在文件路径",  # 中文提示
                    "label": "文件路径"  # 界面显示标签
                }),
                "文件索引": ("INT", {  # 参数名改为中文
                    "default": 0,
                    "min": -1,
                    "max": 9999,
                    "step": 1,
                    "display": "number",
                    "label": "文件索引（-1加载全部）"  # 补充说明
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("文本",)  # 输出端口中文标签
    FUNCTION = "load_txt_files"
    CATEGORY = "👻幻影工具"  # 分类名称优化

    def load_txt_files(self, 文件路径, 文件索引):  # 方法参数同步改为中文
        try:
            if not os.path.exists(文件路径):
                return ("错误：路径不存在",)
            
            txt_pattern = os.path.join(文件路径, "*.txt")
            txt_files = sorted(glob.glob(txt_pattern))
            
            if not txt_files:
                return ("错误：未找到TXT文件",)
            
            if 文件索引 == -1:  # 加载所有文件
                contents = []
                for i, file_path in enumerate(txt_files):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            contents.append(f"--- 文件 {i}：{os.path.basename(file_path)} ---\n{content}")
                    except Exception as e:
                        contents.append(f"读取失败 {file_path}：{str(e)}")
                return ("\n\n".join(contents),)
            else:  # 加载指定索引文件
                if 0 <= 文件索引 < len(txt_files):
                    with open(txt_files[文件索引], 'r', encoding='utf-8') as f:
                        return (f.read(),)
                else:
                    return (f"错误：索引超出范围（共{len(txt_files)}个文件，索引范围0~{len(txt_files)-1}）",)
                    
        except Exception as e:
            return (f"加载错误：{str(e)}",)
