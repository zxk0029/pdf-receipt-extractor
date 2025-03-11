import sys
import os
import time

from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QProgressBar)
from PySide6.QtCore import Qt, QThread, Signal


def import_pdf_processor():
    """延迟导入 PDF 处理模块"""
    from split_pdf_opencv import process_pdf_with_opencv
    return process_pdf_with_opencv

def setup_poppler_path():
    """设置poppler环境"""
    # print(f"当前操作系统: {sys.platform}")
    # print(f"当前PATH: {os.environ.get('PATH', '')}")
    
    if sys.platform == "win32":
        # 获取应用程序的运行路径
        if getattr(sys, 'frozen', False):
            # 如果是打包后的应用
            base_path = sys._MEIPASS
        else:
            # 如果是开发环境
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        # 将poppler的路径添加到环境变量
        os.environ['PATH'] = base_path + os.pathsep + os.environ.get('PATH', '')
    elif sys.platform == "darwin":  # macOS
        # 添加Homebrew安装的poppler路径
        brew_poppler_path = "/opt/homebrew/bin"
        intel_poppler_path = "/usr/local/bin"
        
        # print(f"检查 M1/M2 Mac poppler路径: {brew_poppler_path}")
        # print(f"检查 Intel Mac poppler路径: {intel_poppler_path}")
        
        # 检查路径是否存在并添加到PATH
        if os.path.exists(brew_poppler_path):
            # print(f"找到 M1/M2 Mac poppler")
            os.environ['PATH'] = brew_poppler_path + os.pathsep + os.environ.get('PATH', '')
        if os.path.exists(intel_poppler_path):
            # print(f"找到 Intel Mac poppler")
            os.environ['PATH'] = intel_poppler_path + os.pathsep + os.environ.get('PATH', '')
            
    # print(f"更新后的PATH: {os.environ.get('PATH', '')}")
    
    # 验证poppler是否可用
    try:
        from pdf2image.pdf2image import pdfinfo_from_path
        print("pdf2image 库加载成功")
    except Exception as e:
        print(f"pdf2image 库加载失败: {str(e)}")
        
    # 检查 pdftoppm 是否在路径中
    import shutil
    pdftoppm_path = shutil.which('pdftoppm')
    # print(f"pdftoppm 路径: {pdftoppm_path}")

class PDFProcessThread(QThread):
    progress = Signal(int, str)  # 进度信号：(进度值, 描述文本)
    finished = Signal(bool, str)  # 完成信号：(是否成功, 消息)

    def __init__(self, input_pdf, output_path):
        super().__init__()
        self.input_pdf = input_pdf
        self.output_path = output_path

    def run(self):
        try:
            # 在实际需要时才导入处理模块
            process_pdf_with_opencv = import_pdf_processor()
            
            # 定义进度回调函数
            def progress_callback(value, text):
                self.progress.emit(value, text)
            
            # 处理PDF文件
            process_pdf_with_opencv(
                self.input_pdf,
                self.output_path,
                progress_callback=progress_callback
            )
            
            self.finished.emit(True, "处理完成！")
        except Exception as e:
            self.finished.emit(False, f"处理失败: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF回执单分割工具")
        self.setMinimumSize(600, 400)
        
        # 创建主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 添加说明文字
        intro_label = QLabel(
            "这个工具可以自动检测和分割PDF文件中的回执单。\n"
            "每个回执单将被提取并保存到一个新的PDF文件中。"
        )
        intro_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(intro_label)
        
        # 文件选择部分
        file_layout = QHBoxLayout()
        self.file_label = QLabel("未选择文件")
        self.select_file_btn = QPushButton("选择PDF文件")
        self.select_file_btn.clicked.connect(self.select_input_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.select_file_btn)
        layout.addLayout(file_layout)
        
        # 输出目录选择部分
        output_layout = QHBoxLayout()
        self.output_label = QLabel("未选择输出目录")
        self.select_output_btn = QPushButton("选择输出目录")
        self.select_output_btn.clicked.connect(self.select_output_dir)
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.select_output_btn)
        layout.addLayout(output_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("请选择PDF文件和输出目录")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 处理按钮
        self.process_btn = QPushButton("开始处理")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)
        layout.addWidget(self.process_btn)
        
        # 初始化变量
        self.input_pdf = None
        self.output_dir = None
        self.is_processing = False
        
    def select_input_file(self):
        if self.is_processing:
            return
            
        file_name, _ = QFileDialog.getOpenFileName(
            self, "选择PDF文件", "", "PDF文件 (*.pdf)"
        )
        if file_name:
            self.input_pdf = file_name
            self.file_label.setText(os.path.basename(file_name))
            self.status_label.setText("已选择文件：" + os.path.basename(file_name))
            self.update_process_button()
            
    def select_output_dir(self):
        if self.is_processing:
            return
            
        dir_name = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_name:
            self.output_dir = dir_name
            self.output_label.setText(dir_name)
            self.status_label.setText("已选择输出目录：" + dir_name)
            self.update_process_button()
            
    def update_process_button(self):
        can_process = bool(self.input_pdf and self.output_dir)
        self.process_btn.setEnabled(can_process and not self.is_processing)
        if can_process:
            self.status_label.setText('准备就绪，点击"开始处理"按钮开始处理')
            self.status_label.setStyleSheet("")
            self.progress_bar.setValue(0)  # 重置进度条
        
    def start_processing(self):
        if not self.input_pdf or not self.output_dir or self.is_processing:
            return
            
        # 设置处理中状态
        self.is_processing = True
        self.process_btn.setEnabled(False)
        self.select_file_btn.setEnabled(False)
        self.select_output_btn.setEnabled(False)
        self.status_label.setStyleSheet("")
        self.status_label.setText("正在处理中，请稍候...")
        self.progress_bar.setValue(0)  # 重置进度条
        
        output_path = os.path.join(
            self.output_dir, 
            "merged_receipts.pdf"
        )
        
        # 创建处理线程
        self.thread = PDFProcessThread(self.input_pdf, output_path)
        self.thread.progress.connect(self.update_progress)  # 连接进度信号
        self.thread.finished.connect(self.on_process_finished)
        self.thread.start()
        
    def update_progress(self, value, text):
        """更新进度条和状态文本"""
        self.progress_bar.setValue(value)
        self.status_label.setText(text)
        
    def on_process_finished(self, success, message):
        # 恢复按钮状态
        self.is_processing = False
        self.select_file_btn.setEnabled(True)
        self.select_output_btn.setEnabled(True)
        
        # 更新状态显示
        self.status_label.setText(message)
        if success:
            self.status_label.setStyleSheet("color: green")
            self.progress_bar.setValue(100)  # 确保进度条显示完成
            # 处理成功后，需要选择新文件才能继续处理
            self.input_pdf = None
            self.file_label.setText("请选择新的PDF文件")
        else:
            self.status_label.setStyleSheet("color: red")
            # 处理失败后，允许重试
            self.process_btn.setEnabled(True)

def main():
    # print(f"[{time.time()}] 开始设置环境...")
    # 设置poppler环境
    setup_poppler_path()
    # print(f"[{time.time()}] 环境设置完成")
    
    # print(f"[{time.time()}] 创建应用实例...")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    # print(f"[{time.time()}] 应用启动完成")
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 