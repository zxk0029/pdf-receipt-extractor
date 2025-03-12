from pypdf import PdfWriter, PdfReader
import os

def test_direct_save(input_pdf, output_pdf):
    """测试直接读取和保存，验证是否会失真"""
    print("测试1: 直接读取和保存")
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    
    # 直接复制所有页面
    for page in reader.pages:
        writer.add_page(page)
    
    # 保存
    with open(output_pdf, 'wb') as f:
        writer.write(f)
    
    print(f"原始文件大小: {os.path.getsize(input_pdf) / 1024:.2f}KB")
    print(f"新文件大小: {os.path.getsize(output_pdf) / 1024:.2f}KB")

def test_crop(input_pdf, output_pdf):
    """测试裁剪功能，验证是否会影响质量"""
    print("\n测试2: 使用cropbox裁剪")
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    
    # 获取第一页并裁剪
    page = reader.pages[0]
    
    # 获取原始尺寸
    original_width = float(page.mediabox.width)
    original_height = float(page.mediabox.height)
    
    # 裁剪为上半页（示例）
    page.cropbox.lower_left = (0, original_height/2)
    page.cropbox.upper_right = (original_width, original_height)
    
    writer.add_page(page)
    
    # 保存
    with open(output_pdf, 'wb') as f:
        writer.write(f)
    
    print(f"原始文件大小: {os.path.getsize(input_pdf) / 1024:.2f}KB")
    print(f"裁剪后文件大小: {os.path.getsize(output_pdf) / 1024:.2f}KB")

def main():
    input_pdf = "./receipts.pdf"  # 使用您的测试PDF
    
    # 确保输出目录存在
    os.makedirs("./test_output", exist_ok=True)
    
    # 测试1：直接读取和保存
    test_direct_save(input_pdf, "./test_output/test1_direct_save.pdf")
    
    # 测试2：裁剪
    test_crop(input_pdf, "./test_output/test2_cropped.pdf")

if __name__ == "__main__":
    main() 