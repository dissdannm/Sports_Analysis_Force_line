from __future__ import annotations

import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import AppConfig
from app.main import main as run_local_detection
from core.motion_registry import MotionRegistry


class MotionClientGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("运动力线分析 - 简易客户端")
        self.root.geometry("560x360")
        self.root.resizable(False, False)

        self.config = AppConfig()
        self.registry = MotionRegistry(self.config.motions_dir)

        self.motion_items: list[tuple[str, str]] = []
        self.motion_map: dict[str, str] = {}
        self.runner_thread: threading.Thread | None = None
        self.running = False
        self.ui_queue: queue.Queue[tuple[str, str]] = queue.Queue()

        self.motion_var = tk.StringVar()
        self.status_var = tk.StringVar(value="状态：待机")
        self.tip_var = tk.StringVar(value="说明：选择动作后点击“开始检测”，在摄像头窗口按 ESC 结束。")

        self._build_ui()
        self._load_motions()
        self._poll_ui_queue()

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=18)
        container.pack(fill=tk.BOTH, expand=True)

        title = ttk.Label(container, text="运动力线分析系统（简易 GUI）", font=("Microsoft YaHei UI", 14, "bold"))
        title.pack(anchor=tk.W)

        desc = ttk.Label(
            container,
            text="用于软著演示：动作选择 -> 开始摄像头检测 -> 实时显示分析结果（OpenCV 窗口）。",
            foreground="#475569",
        )
        desc.pack(anchor=tk.W, pady=(6, 16))

        row = ttk.Frame(container)
        row.pack(fill=tk.X)

        ttk.Label(row, text="动作选择：", width=10).pack(side=tk.LEFT)
        self.motion_combo = ttk.Combobox(row, textvariable=self.motion_var, state="readonly", width=44)
        self.motion_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_row = ttk.Frame(container)
        btn_row.pack(fill=tk.X, pady=(14, 0))

        self.start_btn = ttk.Button(btn_row, text="开始检测", command=self._start_detection)
        self.start_btn.pack(side=tk.LEFT)

        self.stop_hint_btn = ttk.Button(btn_row, text="如何停止", command=self._show_stop_hint)
        self.stop_hint_btn.pack(side=tk.LEFT, padx=(10, 0))

        refresh_btn = ttk.Button(btn_row, text="刷新动作", command=self._load_motions)
        refresh_btn.pack(side=tk.LEFT, padx=(10, 0))

        explain_btn = ttk.Button(btn_row, text="软件用途", command=self._show_purpose)
        explain_btn.pack(side=tk.LEFT, padx=(10, 0))

        status = ttk.Label(container, textvariable=self.status_var, foreground="#0f172a")
        status.pack(anchor=tk.W, pady=(22, 6))

        tip = ttk.Label(container, textvariable=self.tip_var, foreground="#64748b")
        tip.pack(anchor=tk.W)

        text = tk.Text(container, height=8, wrap=tk.WORD, borderwidth=1, relief=tk.SOLID)
        text.pack(fill=tk.BOTH, expand=True, pady=(16, 0))
        text.insert(
            tk.END,
            "本软件核心流程：\n"
            "1) 选择动作（如俯卧撑、仰卧起坐、臀桥）；\n"
            "2) 启动摄像头采集人体关键点；\n"
            "3) 计算关节角度、姿态偏移和力线指标；\n"
            "4) 实时给出告警提示与语音反馈；\n"
            "5) 会话结束后导出 CSV 与 JSON 结果。\n",
        )
        text.configure(state=tk.DISABLED)

    def _load_motions(self) -> None:
        try:
            self.registry.load_all()
            ids = self.registry.list_motion_ids()
            items: list[tuple[str, str]] = []
            for motion_id in ids:
                motion = self.registry.get_motion(motion_id)
                label = f"{motion.motion_name} ({motion.motion_id})"
                items.append((label, motion_id))

            self.motion_items = items
            self.motion_map = {label: motion_id for label, motion_id in items}
            labels = [label for label, _ in items]
            self.motion_combo["values"] = labels

            if labels:
                self.motion_var.set(labels[0])
                self.status_var.set(f"状态：已加载 {len(labels)} 个动作")
            else:
                self.motion_var.set("")
                self.status_var.set("状态：未找到动作配置")
        except Exception as exc:  # pragma: no cover - GUI runtime protection
            self.status_var.set("状态：动作加载失败")
            messagebox.showerror("加载失败", f"无法读取动作配置：\n{exc}")

    def _start_detection(self) -> None:
        if self.running:
            messagebox.showinfo("运行中", "检测已在运行。请到摄像头窗口按 ESC 后再启动新任务。")
            return

        selected_label = self.motion_var.get().strip()
        if not selected_label:
            messagebox.showwarning("未选择动作", "请先选择一个动作。")
            return

        motion_id = self.motion_map.get(selected_label)
        if not motion_id:
            messagebox.showwarning("动作无效", "当前动作无法识别，请点击“刷新动作”。")
            return

        self.running = True
        self.start_btn.configure(state=tk.DISABLED)
        self.status_var.set(f"状态：检测中 ({motion_id})")
        self.tip_var.set("说明：请在弹出的摄像头窗口按 ESC 结束检测。")

        self.runner_thread = threading.Thread(
            target=self._run_detection_worker,
            args=(motion_id,),
            daemon=True,
        )
        self.runner_thread.start()

    def _run_detection_worker(self, motion_id: str) -> None:
        try:
            run_local_detection(preferred_motion_id=motion_id, interactive_select=False)
            self.ui_queue.put(("done", f"状态：检测已结束 ({motion_id})"))
        except Exception as exc:  # pragma: no cover - GUI runtime protection
            self.ui_queue.put(("error", f"检测启动失败：{exc}"))
        finally:
            self.ui_queue.put(("unlock", ""))

    def _poll_ui_queue(self) -> None:
        try:
            while True:
                msg_type, payload = self.ui_queue.get_nowait()
                if msg_type == "done":
                    self.status_var.set(payload)
                elif msg_type == "error":
                    self.status_var.set("状态：检测失败")
                    messagebox.showerror("运行失败", payload)
                elif msg_type == "unlock":
                    self.running = False
                    self.start_btn.configure(state=tk.NORMAL)
                    self.tip_var.set("说明：选择动作后点击“开始检测”，在摄像头窗口按 ESC 结束。")
        except queue.Empty:
            pass
        finally:
            self.root.after(200, self._poll_ui_queue)

    @staticmethod
    def _show_stop_hint() -> None:
        messagebox.showinfo("停止方式", "检测启动后会打开摄像头窗口，请在该窗口按 ESC 停止。")

    @staticmethod
    def _show_purpose() -> None:
        messagebox.showinfo(
            "软件用途",
            "本软件用于运动动作视觉检测与力线分析。\n\n"
            "它通过摄像头采集人体关键点，实时计算关节角度与姿态偏移，"
            "并给出告警与语音提示，帮助规范动作。",
        )


def launch() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    try:
        style.theme_use("vista")
    except tk.TclError:
        pass
    MotionClientGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch()
