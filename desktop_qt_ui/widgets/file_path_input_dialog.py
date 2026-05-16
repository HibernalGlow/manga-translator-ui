"""
文件路径输入对话框
支持通过输入多个文件路径或从剪贴板读取文件路径
"""
import os
from typing import List, Optional
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QClipboard, QGuiApplication


class FilePathInputDialog(QDialog):
    """文件路径输入对话框"""
    
    def __init__(self, parent=None, t_func=None):
        """
        初始化对话框
        
        Args:
            parent: 父窗口
            t_func: 翻译函数
        """
        super().__init__(parent)
        self.t_func = t_func or (lambda x: x)
        self.setWindowTitle(self.t_func("Add Files by Path"))
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        
        # 说明标签
        info_label = QLabel(
            self.t_func("Enter file paths (one per line) or paste from clipboard:")
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 文本输入框
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(
            self.t_func(
                "Enter file paths here...\n"
                "Example:\n"
                "C:\\Users\\User\\Pictures\\image1.jpg\n"
                "C:\\Users\\User\\Pictures\\image2.png\n"
                "D:\\Manga\\chapter1.zip"
            )
        )
        self.text_edit.setAcceptRichText(False)
        layout.addWidget(self.text_edit)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 从剪贴板粘贴按钮
        self.paste_button = QPushButton(self.t_func("Paste from Clipboard"))
        self.paste_button.clicked.connect(self._paste_from_clipboard)
        button_layout.addWidget(self.paste_button)
        
        # 清空按钮
        self.clear_button = QPushButton(self.t_func("Clear"))
        self.clear_button.clicked.connect(self.text_edit.clear)
        button_layout.addWidget(self.clear_button)
        
        button_layout.addStretch()
        
        # 取消按钮
        self.cancel_button = QPushButton(self.t_func("Cancel"))
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        # 确定按钮
        self.ok_button = QPushButton(self.t_func("Add Files"))
        self.ok_button.clicked.connect(self._on_ok_clicked)
        self.ok_button.setDefault(True)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
    
    def _paste_from_clipboard(self):
        """从剪贴板粘贴"""
        clipboard = QGuiApplication.clipboard()
        text = clipboard.text()
        
        if text:
            # 如果已有内容，添加换行
            current_text = self.text_edit.toPlainText()
            if current_text and not current_text.endswith('\n'):
                self.text_edit.append('')
            
            self.text_edit.insertPlainText(text)
    
    def _on_ok_clicked(self):
        """确定按钮点击"""
        text = self.text_edit.toPlainText().strip()
        
        if not text:
            QMessageBox.warning(
                self,
                self.t_func("Warning"),
                self.t_func("Please enter at least one file path.")
            )
            return
        
        # 解析文件路径
        paths = self._parse_paths(text)
        
        if not paths:
            QMessageBox.warning(
                self,
                self.t_func("Warning"),
                self.t_func("No valid file paths found.")
            )
            return
        
        # 检查文件是否存在
        valid_paths = []
        invalid_paths = []
        
        for path in paths:
            if os.path.exists(path):
                valid_paths.append(path)
            else:
                invalid_paths.append(path)
        
        if invalid_paths:
            # 显示无效路径警告
            invalid_list = '\n'.join(invalid_paths[:10])
            if len(invalid_paths) > 10:
                invalid_list += f"\n... and {len(invalid_paths) - 10} more"
            
            reply = QMessageBox.question(
                self,
                self.t_func("Some Files Not Found"),
                self.t_func(
                    "The following file(s) do not exist:\n\n{invalid_list}\n\n"
                    "Do you want to add the {valid_count} valid file(s)?"
                ).format(
                    invalid_list=invalid_list,
                    valid_count=len(valid_paths)
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                return
        
        if valid_paths:
            self.file_paths = valid_paths
            self.accept()
        else:
            QMessageBox.warning(
                self,
                self.t_func("Warning"),
                self.t_func("No valid file paths found.")
            )
    
    def _parse_paths(self, text: str) -> List[str]:
        """
        解析文本中的文件路径
        
        Args:
            text: 输入文本
            
        Returns:
            文件路径列表
        """
        paths = []
        
        # 按行分割
        lines = text.split('\n')
        
        for line in lines:
            # 去除首尾空白
            line = line.strip()
            
            # 跳过空行
            if not line:
                continue
            
            # 去除引号（如果有）
            if (line.startswith('"') and line.endswith('"')) or \
               (line.startswith("'") and line.endswith("'")):
                line = line[1:-1]
            
            # 规范化路径
            path = os.path.normpath(line)
            
            # 添加到列表
            if path not in paths:
                paths.append(path)
        
        return paths
    
    def get_file_paths(self) -> List[str]:
        """
        获取文件路径列表
        
        Returns:
            文件路径列表
        """
        return getattr(self, 'file_paths', [])


def add_files_from_clipboard(parent=None, t_func=None) -> Optional[List[str]]:
    """
    从剪贴板添加文件
    
    Args:
        parent: 父窗口
        t_func: 翻译函数
        
    Returns:
        文件路径列表，如果取消则返回 None
    """
    clipboard = QGuiApplication.clipboard()
    mime = clipboard.mimeData()
    
    # 优先处理文件 URL（从资源管理器复制的文件）
    if mime.hasUrls():
        urls = mime.urls()
        file_paths = []
        for url in urls:
            if url.isLocalFile():
                file_path = url.toLocalFile()
                if file_path not in file_paths:
                    file_paths.append(file_path)
        
        if file_paths:
            return file_paths
    
    # 如果没有 URL，处理文本
    text = clipboard.text()
    
    if not text:
        QMessageBox.information(
            parent,
            t_func("Clipboard is Empty") if t_func else "Clipboard is Empty",
            t_func("No text found in clipboard.") if t_func else "No text found in clipboard."
        )
        return None
    
    # 创建对话框并预填充剪贴板内容
    dialog = FilePathInputDialog(parent, t_func)
    dialog.text_edit.setPlainText(text)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_file_paths()
    
    return None
