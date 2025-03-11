import os
import sys
import shutil
import urllib.request
import zipfile
import subprocess
from pathlib import Path

def check_poppler_installed():
    """检查系统是否已安装 Poppler"""
    if sys.platform != 'win32':
        return None  # 非 Windows 系统不需要检查
        
    # 检查常见的 Poppler 安装路径
    common_paths = [
        os.path.expandvars("%ProgramFiles%\\poppler"),
        os.path.expandvars("%ProgramFiles(x86)%\\poppler"),
        os.path.expandvars("%LocalAppData%\\poppler-windows\\Library\\bin"),
        "C:\\poppler\\bin",
        "C:\\Program Files\\poppler\\bin",
        "C:\\Program Files (x86)\\poppler\\bin"
    ]
    
    # 检查环境变量 PATH
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    common_paths.extend([p for p in path_dirs if "poppler" in p.lower()])
    
    # 检查每个可能的路径
    for path in common_paths:
        if os.path.exists(path):
            pdftoppm_path = os.path.join(path, "pdftoppm.exe")
            if os.path.exists(pdftoppm_path):
                print(f"找到已安装的 Poppler: {path}")
                return path
    
    return None

def check_environment():
    """检查并安装必要的依赖"""
    try:
        # 检查是否存在 requirements.txt
        if not os.path.exists('requirements.txt'):
            print("错误：未找到 requirements.txt 文件")
            sys.exit(1)
            
        # 安装依赖
        print("安装项目依赖...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        # 安装 PyInstaller（如果需要）
        try:
            import PyInstaller
        except ImportError:
            print("安装 PyInstaller...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            
    except subprocess.CalledProcessError as e:
        print(f"安装依赖时出错：{e}")
        sys.exit(1)

def download_poppler_for_windows():
    """下载并解压Windows版本的poppler"""
    # 首先检查是否已安装
    existing_poppler = check_poppler_installed()
    if existing_poppler:
        return existing_poppler
        
    # 检查是否已经手动下载了zip文件
    zip_path = "poppler-windows.zip"
    extract_path = "poppler-windows"
    
    if not os.path.exists(zip_path):
        print("未找到已下载的 poppler-windows.zip，开始下载...")
        try:
            poppler_url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.08.0-0/Release-24.08.0-0.zip"
            print("下载poppler...")
            urllib.request.urlretrieve(poppler_url, zip_path)
        except Exception as e:
            print(f"下载 Poppler 时出错：{e}")
            return None
    else:
        print("检测到已下载的 poppler-windows.zip")
    
    try:
        # 解压poppler
        if not os.path.exists(extract_path):
            print("解压poppler...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
        
        return os.path.join(extract_path, "Library", "bin")
    except Exception as e:
        print(f"解压 Poppler 时出错：{e}")
        return None

def build_app():
    """打包应用程序"""
    # 确保环境准备就绪
    check_environment()
    
    # 检查源文件是否存在
    src_file = os.path.join("src", "pdf_splitter_gui.py")
    if not os.path.exists(src_file):
        print(f"错误：找不到源文件 {src_file}")
        sys.exit(1)
    
    # 动态导入 PyInstaller
    import PyInstaller.__main__
    
    # 准备构建参数
    build_args = [
        src_file,  # 主程序文件
        '--name=PDF回执单分割工具',  # 应用名称
        '--onefile',  # 打包成单个文件
        '--windowed',  # 不显示控制台窗口
        '--clean',  # 清理临时文件
        '--noconfirm',  # 不确认覆盖
    ]
    
    # 添加图标
    if sys.platform == 'darwin':  # macOS
        if os.path.exists('icon.icns'):
            build_args.append('--icon=icon.icns')
    elif sys.platform == 'win32':  # Windows
        if os.path.exists('icon.ico'):
            build_args.append('--icon=icon.ico')
        
        # 下载并准备poppler
        poppler_path = download_poppler_for_windows()
        if poppler_path:
            # 添加poppler相关文件
            build_args.extend([
                f'--add-binary={poppler_path}/*.dll;.',
                f'--add-binary={poppler_path}/pdftoppm.exe;.',
                f'--add-binary={poppler_path}/pdftocairo.exe;.',
            ])
        else:
            print("警告：Poppler 配置失败，Windows 版本可能无法正常工作")
    else:  # Linux
        if os.path.exists('icon.png'):
            build_args.append('--icon=icon.png')
    
    # 添加其他资源文件
    if os.path.exists('README.md'):
        build_args.append('--add-data=README.md:.')
    
    # 添加源代码目录到 Python 路径
    build_args.extend([
        '--paths=src',
        f'--add-data=src/split_pdf_opencv.py{os.pathsep}.'
    ])
    
    try:
        # 运行PyInstaller
        print("开始打包...")
        PyInstaller.__main__.run(build_args)
        
        # 清理临时文件
        print("\n是否需要清理临时文件？")
        print("1. poppler-windows.zip 是手动下载的文件，建议保留")
        print("2. poppler-windows 目录是解压的临时文件，可以删除")
        
        # 只删除解压的临时目录
        if os.path.exists('poppler-windows'):
            try:
                shutil.rmtree('poppler-windows')
                print("已清理临时解压的 poppler-windows 目录")
            except Exception as e:
                print(f"清理临时文件时出错：{e}")
            
        print("\n打包完成！")
        if sys.platform == 'darwin':
            print("可执行文件位于: dist/PDF回执单分割工具.app")
        elif sys.platform == 'win32':
            print("可执行文件位于: dist/PDF回执单分割工具.exe")
        else:
            print("可执行文件位于: dist/PDF回执单分割工具")
            
    except Exception as e:
        print(f"打包过程出错：{e}")
        sys.exit(1)

if __name__ == '__main__':
    build_app() 