"""
👻幻影工具 - 视频首尾帧获取节点
最终修复版：兼容VideoFromFile/VideoFromComponents，优先调用官方方法获取帧，解决无有效帧数据异常
"""
import cv2
import numpy as np
import torch
import os
import warnings
from typing import Tuple

# 忽略无关警告，避免日志刷屏
warnings.filterwarnings("ignore")

class VideoFrameExtractNode:
    # 节点核心配置
    CATEGORY = "👻幻影工具"
    FUNCTION = "extract_first_last_frame"
    RETURN_TYPES = ("IMAGE", "IMAGE")
    RETURN_NAMES = ("首帧图像", "尾帧图像")
    OUTPUT_NODE = True  # 支持预览

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "视频路径": ("STRING", {
                    "default": "",
                    "tooltip": "可选-视频文件路径（优先级高于视频输入端口），支持mp4/avi/mov/mkv/flv格式"
                })
            },
            "optional": {
                "视频": ("*", {
                    "forceInput": False,
                    "tooltip": "可选连-ComfyUI视频对象（VideoFromFile/VideoFromComponents/ndarray帧序列）"
                })
            }
        }

    def _cv2frame2comfy(self, frame: np.ndarray) -> torch.Tensor:
        """cv2帧转ComfyUI标准IMAGE格式（float32/0-1/[1,H,W,3]）"""
        if frame is None or frame.size == 0:
            raise Exception("无法获取有效帧数据")
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) if frame.shape[-1] == 3 else frame
        frame_norm = frame_rgb.astype(np.float32) / 255.0
        return torch.from_numpy(np.expand_dims(frame_norm, axis=0))

    def _get_video_path(self, video_obj) -> str:
        """从VideoFromFile提取有效视频文件路径（兜底逻辑）"""
        video_path = None
        if hasattr(video_obj, 'get_stream_source'):
            try:
                src = video_obj.get_stream_source()
                if isinstance(src, str) and os.path.exists(src) and src.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv')):
                    video_path = src
            except:
                pass
        if not video_path:
            for attr in dir(video_obj):
                if attr.startswith('_'):
                    continue
                try:
                    val = getattr(video_obj, attr)
                    if isinstance(val, str) and os.path.exists(val) and val.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv')):
                        video_path = val
                        break
                except:
                    pass
        return video_path

    def _read_cv2_frame(self, video_path: str, frame_idx: int) -> np.ndarray:
        """CV2读取指定帧，重试+资源释放，解决IO连接异常"""
        for retry in range(2):
            cap = None
            try:
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    raise Exception("CV2无法打开视频")
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx - 1 if frame_idx > 0 else 0)
                ret, frame = cap.read()
                if ret and frame is not None:
                    return frame
                else:
                    raise Exception(f"读取帧{frame_idx}失败")
            except Exception as e:
                if retry == 1:
                    raise Exception(f"重试后仍无法读取帧{frame_idx}：{str(e)}")
            finally:
                if cap:
                    cap.release()
        return None

    def _scan_nested_obj(self, obj, frame_attrs, depth=0):
        """递归扫描嵌套对象，提取帧数据（核心修复：处理多层嵌套）"""
        video_frames = None
        max_depth = 3  # 限制递归深度，避免死循环
        if depth > max_depth:
            return None
        
        # 直接匹配tensor/ndarray且维度为4（帧数,H,W,3）
        if isinstance(obj, (np.ndarray, torch.Tensor)) and len(obj.shape) == 4:
            return obj
        
        # 扫描当前对象的指定属性
        for attr in frame_attrs:
            if hasattr(obj, attr):
                try:
                    val = getattr(obj, attr)
                    # 匹配帧数据格式
                    if isinstance(val, (np.ndarray, torch.Tensor)) and len(val.shape) == 4:
                        print(f"✅ 从嵌套属性.{attr}（深度{depth}）提取到帧数据 | shape：{val.shape}")
                        return val
                    # 非帧数据但为对象/字典，继续递归
                    elif isinstance(val, (object, dict)) and not isinstance(val, (str, int, float, bool)):
                        nested_frames = self._scan_nested_obj(val, frame_attrs, depth + 1)
                        if nested_frames is not None:
                            return nested_frames
                except:
                    continue
        
        # 处理字典类型的嵌套（部分自定义实现会用字典存储components）
        if isinstance(obj, dict):
            for key, val in obj.items():
                if key in frame_attrs:
                    if isinstance(val, (np.ndarray, torch.Tensor)) and len(val.shape) == 4:
                        print(f"✅ 从字典key.{key}（深度{depth}）提取到帧数据 | shape：{val.shape}")
                        return val
                elif isinstance(val, (object, dict)) and not isinstance(val, (str, int, float, bool)):
                    nested_frames = self._scan_nested_obj(val, frame_attrs, depth + 1)
                    if nested_frames is not None:
                        return nested_frames
        return None

    def _extract_from_components(self, comp_obj) -> Tuple[torch.Tensor, torch.Tensor]:
        """从VideoFromComponents提取帧序列：强化递归扫描+全链路兜底"""
        video_frames = None

        # ====================== 第一步：优先调用官方方法获取帧 ======================
        try:
            # 1. 获取总帧数，验证视频有效性
            total_frames = comp_obj.get_frame_count()
            if total_frames <= 0:
                raise Exception("VideoFromComponents返回总帧数为0")
            
            # 2. 递归扫描get_components()返回值（核心修复：处理嵌套结构）
            components = comp_obj.get_components()
            if components:
                frame_attrs = ["frames", "frame_data", "video_frames", "video_data", "tensor", "data"]
                video_frames = self._scan_nested_obj(components, frame_attrs)
            
            # 3. 兜底1：调用get_frame逐帧读取（标准接口）
            if video_frames is None and hasattr(comp_obj, 'get_frame'):
                print("⚠️ 未从components提取到帧，尝试get_frame逐帧读取")
                frame_list = []
                max_read_frames = min(total_frames, 1000)  # 限制最大读取数，避免卡死
                for idx in range(max_read_frames):
                    frame = comp_obj.get_frame(idx)
                    if frame is None:
                        break  # 帧读取失败则终止
                    # 统一格式为ndarray
                    if isinstance(frame, torch.Tensor):
                        frame = frame.cpu().numpy()
                    if isinstance(frame, np.ndarray) and len(frame.shape) == 3:
                        frame_list.append(frame)
                if frame_list:
                    video_frames = np.stack(frame_list)
                    print(f"✅ 逐帧读取完成，共获取{len(frame_list)}帧 | shape：{video_frames.shape}")
                else:
                    raise Exception("get_frame逐帧读取无有效数据")
            
            # 4. 兜底2：尝试__getitem__索引读取（兼容自定义实现）
            if video_frames is None and hasattr(comp_obj, '__getitem__'):
                print("⚠️ get_frame读取失败，尝试__getitem__索引读取")
                frame_list = []
                max_read_frames = min(total_frames, 1000)
                for idx in range(max_read_frames):
                    try:
                        frame = comp_obj[idx]
                        if isinstance(frame, torch.Tensor):
                            frame = frame.cpu().numpy()
                        if isinstance(frame, np.ndarray) and len(frame.shape) == 3:
                            frame_list.append(frame)
                        else:
                            break
                    except:
                        break
                if frame_list:
                    video_frames = np.stack(frame_list)
                    print(f"✅ 索引读取完成，共获取{len(frame_list)}帧 | shape：{video_frames.shape}")
                else:
                    raise Exception("__getitem__索引读取无有效数据")

        except Exception as e:
            raise Exception(f"调用官方方法失败：{str(e)}")

        # ====================== 第二步：全属性扫描（最终兜底） ======================
        if video_frames is None:
            frame_candidate_attrs = []
            # 递归扫描所有属性（含嵌套），便于定位帧数据（移除调试日志打印）
            def print_nested_attr(obj, prefix="", depth=0):
                nonlocal frame_candidate_attrs
                if depth > 3:
                    return
                for attr in dir(obj):
                    if attr.startswith('_'):
                        continue
                    try:
                        val = getattr(obj, attr)
                        # 筛选疑似帧属性
                        if (isinstance(val, (np.ndarray, torch.Tensor)) and
                                len(getattr(val, 'shape', [])) in [3, 4]):
                            frame_candidate_attrs.append(f"{prefix.strip()}{attr}")
                            if video_frames is None:
                                video_frames = val
                        # 递归扫描子对象
                        if isinstance(val, (object, dict)) and not isinstance(val, (str, int, float, bool)):
                            print_nested_attr(val, prefix + "  └─", depth + 1)
                    except Exception as e:
                        continue

            print_nested_attr(comp_obj)

        # ====================== 第三步：校验与解析 ======================
        # 无匹配属性的兜底
        if video_frames is None:
            if frame_candidate_attrs:
                raise Exception(f"未匹配到有效帧序列！疑似帧属性：{frame_candidate_attrs}，请检查维度是否为(帧数,H,W,3)")
            else:
                raise Exception("未找到任何疑似帧属性，VideoFromComponents对象无有效帧数据")

        # 格式转换与维度校验
        try:
            # tensor转ndarray（CPU）
            if isinstance(video_frames, torch.Tensor):
                video_frames = video_frames.cpu().numpy()
            # 3维单帧自动补为4维多帧
            if len(video_frames.shape) == 3 and video_frames.shape[-1] == 3:
                video_frames = np.expand_dims(video_frames, axis=0)
                print(f"⚠️ 单帧自动补为4维，新shape：{video_frames.shape}")
            # 必须是4维帧序列（帧数,H,W,3）
            if len(video_frames.shape) != 4:
                raise Exception(f"帧序列维度错误！预期4维(帧数,H,W,3)，实际{len(video_frames.shape)}维，shape：{video_frames.shape}")
            # 提取首尾帧
            first_frame = self._cv2frame2comfy(video_frames[0])
            last_frame = self._cv2frame2comfy(video_frames[-1])
            return (first_frame, last_frame)
        except Exception as e:
            raise Exception(f"帧序列解析失败：{str(e)}")

    def _process_video_path(self, video_path: str) -> Tuple[torch.Tensor, torch.Tensor]:
        """处理视频路径输入，读取首尾帧"""
        if not video_path or not os.path.exists(video_path):
            raise Exception("视频路径无效或不存在")
        if not video_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv')):
            raise Exception("不支持的视频格式，仅支持mp4/avi/mov/mkv/flv")
        
        # 获取总帧数
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception("无法打开视频文件")
        total_frames = max(1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        cap.release()
        
        # 读取首尾帧
        first_frame = self._read_cv2_frame(video_path, 0)
        last_frame = self._read_cv2_frame(video_path, max(0, total_frames - 1))
        
        if first_frame is None:
            raise Exception("无法读取视频首帧")
        if last_frame is None:
            raise Exception("无法读取视频尾帧")
            
        return (self._cv2frame2comfy(first_frame), self._cv2frame2comfy(last_frame))

    def extract_first_last_frame(self, 视频路径="", 视频=None) -> Tuple[torch.Tensor, torch.Tensor]:
        """主执行函数：全类型兼容+全链路异常兜底"""
        # 优先级判断：视频路径有效则优先使用
        try:
            if 视频路径 and os.path.exists(视频路径) and 视频路径.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv')):
                print("✅ 检测到有效视频路径，优先使用路径读取")
                return self._process_video_path(视频路径)
        except Exception as e:
            print(f"⚠️ 视频路径处理失败：{str(e)}，尝试使用视频输入端口数据")
        
        # 视频路径无效/不存在，使用视频输入端口数据
        try:
            # 检查视频输入端口是否有数据
            if 视频 is None:
                raise Exception("视频输入端口无数据且视频路径无效")
            
            # 情况1：直接传入ndarray帧序列
            if isinstance(视频, np.ndarray):
                if len(视频.shape) == 3 and 视频.shape[-1] == 3:
                    视频 = np.expand_dims(视频, axis=0)
                if len(视频.shape) == 4:
                    first_frame = self._cv2frame2comfy(视频[0])
                    last_frame = self._cv2frame2comfy(视频[-1])
                    return (first_frame, last_frame)
                else:
                    raise Exception(f"ndarray帧维度错误，shape：{视频.shape}，预期4维(帧数,H,W,3)")

            # 情况2：VideoFromComponents对象（核心：强化递归扫描）
            video_type = str(type(视频))
            if "VideoFromComponents" in video_type:
                print("✅ 检测到VideoFromComponents，开始扫描属性并解析")
                return self._extract_from_components(视频)

            # 情况3：VideoFromFile对象（兼容原逻辑，修复IO异常）
            elif "VideoFromFile" in video_type:
                print("✅ 检测到VideoFromFile，使用CV2读取首尾帧")
                video_path = self._get_video_path(视频)
                if not video_path or not os.path.exists(video_path):
                    raise Exception("无法从VideoFromFile获取有效视频路径")
                # 双源获取总帧数
                total_frames = 视频.get_frame_count() if (hasattr(视频, 'get_frame_count') and 视频.get_frame_count() > 0) else 0
                if total_frames <= 0:
                    cap = cv2.VideoCapture(video_path)
                    total_frames = max(1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
                    cap.release()
                # 读取首尾帧
                first_frame = self._read_cv2_frame(video_path, 0)
                last_frame = self._read_cv2_frame(video_path, max(0, total_frames - 1))
                
                if first_frame is None:
                    raise Exception("无法读取VideoFromFile首帧")
                if last_frame is None:
                    raise Exception("无法读取VideoFromFile尾帧")
                    
                return (self._cv2frame2comfy(first_frame), self._cv2frame2comfy(last_frame))

            # 情况4：不支持的类型
            else:
                raise Exception(f"不支持的视频类型：{video_type}，仅支持VideoFromFile/VideoFromComponents/ndarray")

        # 捕获所有异常并统一抛出指定提示
        except Exception as e:
            raise Exception(f"无法获取首尾帧信息：{str(e)}")

# 节点注册（与__init__.py保持一致）
NODE_CLASS_MAPPINGS = {
    "VideoFrameExtractNode": VideoFrameExtractNode
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "VideoFrameExtractNode": "视频首尾帧获取"
}