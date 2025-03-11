import os
import sys
import subprocess
import shutil
import urllib.request
import zipfile
from pathlib import Path

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
        
        # 安装 Nuitka（如果需要）
        try:
            import nuitka
        except ImportError:
            print("安装 Nuitka...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "nuitka"])
            
    except subprocess.CalledProcessError as e:
        print(f"安装依赖时出错：{e}")
        sys.exit(1)

def download_poppler():
    """下载并配置 Poppler"""
    poppler_url = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.08.0-0/Release-24.08.0-0.zip"
    zip_path = "poppler-windows.zip"
    extract_path = "poppler-windows"
    
    try:
        # 下载 poppler
        if not os.path.exists(zip_path):
            print("正在下载 Poppler...")
            urllib.request.urlretrieve(poppler_url, zip_path)
        
        # 解压 poppler
        if not os.path.exists(extract_path):
            print("正在解压 Poppler...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
        
        # 获取 bin 目录路径
        poppler_path = os.path.join(extract_path, "Library", "bin")
        
        # 将 poppler 路径添加到环境变量
        os.environ["PATH"] = poppler_path + os.pathsep + os.environ.get("PATH", "")
        
        return poppler_path
    except Exception as e:
        print(f"下载或配置 Poppler 时出错：{e}")
        return None

def build_windows():
    """Windows 平台打包"""
    # 确保环境准备就绪
    check_environment()
    
    # 下载并配置 Poppler
    print("配置 Poppler...")
    poppler_path = download_poppler()
    if not poppler_path:
        print("错误：Poppler 配置失败！")
        sys.exit(1)

    # 创建图标
    icon_path = "app_icon.ico"
    if not os.path.exists(icon_path):
        print("警告: 未找到图标文件 app_icon.ico，将使用默认图标")
        icon_path = None

    # Nuitka 编译命令
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--windows-disable-console",
        "--follow-imports",
        "--enable-plugin=pyside6",
        "--include-package=cv2",
        "--include-package=pdf2image",
        "--include-package=pypdf",
        "--include-package=numpy",
        "--include-package=PIL",
        "--windows-company-name=YourCompany",
        "--windows-product-name=PDF回执单分割工具",
        "--windows-file-version=1.0.0",
        "--windows-product-version=1.0.0",
        "--windows-file-description=PDF回执单自动分割工具",
        "--lto=yes",
        "--jobs=4",
        "--remove-output",
        "--assume-yes-for-downloads",
        "--prefer-source-code"
    ]

    # 添加 Poppler 相关文件
    cmd.extend([
        f"--include-data-dir={poppler_path}=poppler/bin",
    ])

    # 添加图标
    if icon_path:
        cmd.append(f"--windows-icon-from-ico={icon_path}")

    # 添加主程序
    cmd.append("pdf_splitter_gui.py")

    try:
        print("开始编译...")
        subprocess.check_call(cmd)

        # 创建发布目录
        dist_dir = Path("dist")
        dist_dir.mkdir(exist_ok=True)

        # 移动编译后的文件到发布目录
        exe_name = "pdf_splitter_gui.exe"
        if os.path.exists(exe_name):
            shutil.move(exe_name, dist_dir / exe_name)
        
        build_dir = Path("pdf_splitter_gui.dist")
        if build_dir.exists():
            for item in build_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, dist_dir)
                else:
                    shutil.copytree(item, dist_dir / item.name, dirs_exist_ok=True)
            shutil.rmtree(build_dir)

        # 清理临时文件
        print("清理临时文件...")
        if os.path.exists("poppler-windows.zip"):
            os.remove("poppler-windows.zip")
        if os.path.exists("poppler-windows"):
            shutil.rmtree("poppler-windows")

        print(f"\n打包完成！可执行文件位于: {dist_dir / exe_name}")
        print("注意：首次运行可能需要等待几秒钟加载依赖。")
            
    except Exception as e:
        print(f"打包过程出错：{e}")
        sys.exit(1)

if __name__ == "__main__":
    if sys.platform != "win32":
        print("错误：此脚本仅支持 Windows 系统！")
        sys.exit(1)
    
    try:
        build_windows()
    except Exception as e:
        print(f"打包过程出错：{e}")
        sys.exit(1) 