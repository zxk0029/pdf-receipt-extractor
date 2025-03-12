# PDF Receipt Splitter

一个用于自动检测和分割 PDF 文件中回执单的工具。该工具使用 OpenCV 进行智能检测，并通过 PyPDF 进行高质量分割，保持原始 PDF 的清晰度和特性。

## 功能特点

- 自动检测 PDF 中的回执单区域
- 智能分割并保持原始 PDF 质量
  - 保留原始 PDF 的矢量文字和压缩特性
  - 保持文档的清晰度和小体积
  - 仅裁剪高度，保持原始宽度以确保内容完整
- 支持批量处理多个回执单
- 智能识别完整回执单，避免不必要的分割
- 直观的图形用户界面
- 跨平台支持 (Windows, macOS, Linux)

## 项目结构

```
pdf-receipt-splitter/
├── src/                    # 源代码
│   ├── pdf_splitter_gui.py # GUI界面
│   └── split_pdf_opencv.py # PDF处理核心逻辑
├── docs/                   # 文档
├── tests/                  # 测试文件
├── examples/               # 示例文件
├── build.py               # PyInstaller 打包脚本
├── build_windows.py       # Nuitka 打包脚本 (Windows)
├── requirements.txt       # 项目依赖
└── README.md             # 项目说明
```

## 安装说明

### 环境要求

- Python 3.10 或更高版本
- 操作系统：
  - Windows 10/11
  - macOS 11.0 或更高版本
  - Linux (Ubuntu 20.04+)

### 依赖安装

1. 克隆仓库：
   ```bash
   git clone https://github.com/zxk0029/pdf-receipt-extractor.git
   cd pdf-receipt-extractor
   ```

2. 创建虚拟环境：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # 或
   .\\venv\\Scripts\\activate  # Windows
   ```

3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

4. 安装系统依赖：
   - **macOS**:
     ```bash
     brew install poppler
     ```
   - **Windows**:
     - 无需手动安装，打包时会自动下载
   - **Linux**:
     ```bash
     sudo apt-get install poppler-utils
     ```

## 使用说明

1. 运行程序：
   ```bash
   python src/pdf_splitter_gui.py
   ```

2. 在程序界面中：
   - 点击"选择PDF文件"选择要处理的PDF
   - 点击"选择输出目录"选择保存位置
   - 点击"开始处理"开始处理

### 处理说明

程序会智能处理每个页面：
1. 自动检测页面中的回执单区域
2. 智能判断是否需要分割（对于完整回执单会保持原样）
3. 保持原始PDF质量进行分割
4. 生成体积小、清晰度高的输出文件

## 打包说明

### 使用 PyInstaller (体积小启动较慢)

```bash
python build.py
```

### 使用 Nuitka (体积大启动快)

```bash
python build_windows.py
```

## 贡献指南

1. Fork 本仓库
2. 创建您的特性分支 (git checkout -b feature/AmazingFeature)
3. 提交您的更改 (git commit -m 'Add some AmazingFeature')
4. 推送到分支 (git push origin feature/AmazingFeature)
5. 开启一个 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 致谢

- OpenCV 团队
- PyPDF 团队
- PySide6/Qt 团队
- Poppler 开发者 
