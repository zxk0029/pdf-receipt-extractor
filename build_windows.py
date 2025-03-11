import os
import sys
import subprocess
import shutil
import urllib.request
import zipfile
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
    # 首先检查是否已安装
    existing_poppler = check_poppler_installed()
    if existing_poppler:
        return existing_poppler
        
    print("未找到已安装的 Poppler，开始下载...")
    
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

    # 创建临时目录用于存放 Poppler 文件
    temp_poppler_dir = "temp_poppler"
    if os.path.exists(temp_poppler_dir):
        shutil.rmtree(temp_poppler_dir)
    os.makedirs(temp_poppler_dir)
    
    # 复制 Poppler 文件到临时目录
    for file in os.listdir(poppler_path):
        shutil.copy2(os.path.join(poppler_path, file), temp_poppler_dir)

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
        "--prefer-source-code",
        f"--include-data-dir={temp_poppler_dir}=poppler"
    ]

    # 添加图标
    if icon_path:
        cmd.append(f"--windows-icon-from-ico={icon_path}")

    # 添加主程序
    cmd.append("src/pdf_splitter_gui.py")

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
        print("\n是否需要清理临时文件？")
        print("1. poppler-windows.zip 是手动下载的文件，建议保留")
        print("2. poppler-windows 目录是解压的临时文件，可以删除")
        print("3. temp_poppler 是临时目录，将被删除")
        
        # 只删除临时目录
        if os.path.exists("poppler-windows"):
            try:
                shutil.rmtree("poppler-windows")
                print("已清理临时解压的 poppler-windows 目录")
            except Exception as e:
                print(f"清理 poppler-windows 目录时出错：{e}")
                
        if os.path.exists(temp_poppler_dir):
            try:
                shutil.rmtree(temp_poppler_dir)
                print("已清理临时的 temp_poppler 目录")
            except Exception as e:
                print(f"清理 {temp_poppler_dir} 目录时出错：{e}")

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