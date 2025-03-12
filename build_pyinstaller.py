import os
import sys
import shutil
import urllib.request
import zipfile
import subprocess
from pathlib import Path

def check_poppler_installed():
    """检查系统是否已安装 Poppler"""
    if sys.platform == 'darwin':
        # macOS: 检查 brew 安装的 Poppler
        if os.path.exists('/opt/homebrew/bin/pdftoppm'):
            return '/opt/homebrew/bin'
        elif os.path.exists('/usr/local/bin/pdftoppm'):
            return '/usr/local/bin'
        print("警告：未找到 Poppler，请使用 'brew install poppler' 安装")
        sys.exit(1)
    elif sys.platform == 'linux':
        # Linux: 检查系统安装的 Poppler
        if os.path.exists('/usr/bin/pdftoppm'):
            return '/usr/bin'
        print("警告：未找到 Poppler，请使用包管理器安装 poppler-utils")
        sys.exit(1)
    elif sys.platform == 'win32':
        # Windows: 检查常见的 Poppler 安装路径
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

def build_with_pyinstaller():
    """使用 PyInstaller 打包"""
    try:
        # 检查并配置 Poppler
        print("配置 Poppler...")
        poppler_path = None
        temp_poppler_dir = None
        
        if sys.platform == 'win32':
            # Windows 需要下载和配置 Poppler
            poppler_path = download_poppler_for_windows()
            if not poppler_path:
                print("错误：Poppler 配置失败！")
                sys.exit(1)

            # 创建临时目录用于存放 Poppler 文件
            temp_poppler_dir = "temp_poppler"
            if os.path.exists(temp_poppler_dir):
                shutil.rmtree(temp_poppler_dir)
            os.makedirs(temp_poppler_dir)
            
            # 复制 Poppler 文件到临时目录
            if os.path.exists(poppler_path):
                for file in os.listdir(poppler_path):
                    if file.endswith('.dll') or file.endswith('.exe'):
                        shutil.copy2(os.path.join(poppler_path, file), temp_poppler_dir)
        else:
            # macOS 和 Linux 使用系统安装的 Poppler
            poppler_path = check_poppler_installed()
            if not poppler_path:
                print("错误：请先安装 Poppler")
                if sys.platform == 'darwin':
                    print("使用命令：brew install poppler")
                else:
                    print("使用命令：sudo apt-get install poppler-utils")
                sys.exit(1)
        
        # 设置打包参数
        build_args = [
            'src/pdf_splitter_gui.py',  # 主程序文件
            '--name=PDF回执单分割工具',  # 程序名称
            '--noconsole',  # 不显示控制台
            '--clean',  # 清理临时文件
            '--hidden-import=PIL._tkinter_finder',  # 添加隐藏导入
            '--hidden-import=pypdf',
            '--hidden-import=pdf2image',
            '--hidden-import=cv2',
            '--hidden-import=numpy',
        ]
        
        # 在 Windows 下添加 Poppler 文件
        if sys.platform == 'win32' and temp_poppler_dir:
            build_args.extend(['--add-data', f'{temp_poppler_dir};poppler'])
        
        # 如果存在图标文件，添加图标
        if os.path.exists('app_icon.ico'):
            build_args.extend(['--icon=app_icon.ico'])
        
        # 运行PyInstaller
        print("开始打包...")
        PyInstaller.__main__.run(build_args)
        
        # 清理临时文件（仅 Windows）
        if sys.platform == 'win32':
            print("\n是否需要清理临时文件？")
            print("1. poppler-windows.zip 是手动下载的文件，建议保留")
            print("2. poppler-windows 目录是解压的临时文件，可以删除")
            print("3. temp_poppler 是临时目录，将被删除")
            
            # 只删除临时目录
            if os.path.exists('poppler-windows'):
                try:
                    shutil.rmtree('poppler-windows')
                    print("已清理临时解压的 poppler-windows 目录")
                except Exception as e:
                    print(f"清理临时文件时出错：{e}")
                    
            if os.path.exists(temp_poppler_dir):
                try:
                    shutil.rmtree(temp_poppler_dir)
                    print("已清理临时的 temp_poppler 目录")
                except Exception as e:
                    print(f"清理 {temp_poppler_dir} 目录时出错：{e}")
            
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
    build_with_pyinstaller() 