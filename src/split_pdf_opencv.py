from pdf2image import convert_from_path
import cv2
import numpy as np
from PIL import Image
import os
from pypdf import PdfWriter, PdfReader
from io import BytesIO
import sys


def process_pdf_with_opencv(input_pdf, output_path, progress_callback=None):
    """
    使用OpenCV处理PDF文件，检测并分割回执单，将所有回执单保存到一个PDF文件中
    
    Args:
        input_pdf: 输入PDF文件路径
        output_path: 输出PDF文件路径
        progress_callback: 进度回调函数，接收两个参数：(进度百分比, 状态描述)
    """
    if progress_callback:
        progress_callback(0, f"正在处理PDF: {input_pdf}")
    
    # 创建PDF写入器
    pdf_writer = PdfWriter()
    
    # 获取总页数（使用低DPI加快速度）
    if sys.platform == "darwin":
        poppler_path = "/opt/homebrew/bin" if os.path.exists("/opt/homebrew/bin/pdftoppm") else "/usr/local/bin"
        images = convert_from_path(input_pdf, dpi=1, poppler_path=poppler_path)
    else:
        images = convert_from_path(input_pdf, dpi=1)
    total_pages = len(images)
    
    if progress_callback:
        progress_callback(1, f"总页数: {total_pages}")

    # 处理每一页
    for page_num in range(total_pages):
        if progress_callback:
            progress = int((page_num / total_pages) * 98) + 1  # 1-99的进度范围
            progress_callback(progress, f"正在处理第 {page_num + 1}/{total_pages} 页")
        
        # 转换当前页为图像
        if sys.platform == "darwin":
            images = convert_from_path(input_pdf, dpi=300, first_page=page_num+1, 
                                    last_page=page_num+1, poppler_path=poppler_path)
        else:
            images = convert_from_path(input_pdf, dpi=300, first_page=page_num+1, 
                                    last_page=page_num+1)
        img = images[0]
        
        # 转换为OpenCV格式
        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        height, width = cv_img.shape[:2]
        
        # 转换为灰度图
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        
        # 使用自适应阈值处理
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 21, 5
        )
        
        # 进行形态学操作
        kernel = np.ones((7,7), np.uint8)
        dilated = cv2.dilate(binary, kernel, iterations=3)
        eroded = cv2.erode(dilated, kernel, iterations=2)
        
        # 查找轮廓
        contours, hierarchy = cv2.findContours(
            eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        # 降低最小区域面积的要求
        min_area = width * height * 0.1
        
        # 过滤并排序轮廓（按垂直位置）
        valid_contours = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(cnt)
                if 0.15 <= h / height <= 0.45:
                    valid_contours.append(cnt)
        
        # 按y坐标排序
        valid_contours = sorted(
            valid_contours,
            key=lambda c: cv2.boundingRect(c)[1]
        )
        
        if progress_callback:
            progress_callback(progress, f"第 {page_num + 1} 页找到 {len(valid_contours)} 个回执单")
        
        # 处理每个区域
        for idx, cnt in enumerate(valid_contours):
            x, y, w, h = cv2.boundingRect(cnt)
            
            # 添加边距
            margin = 30
            x = max(0, x - margin)
            y = max(0, y - margin)
            w = min(width - x, w + 2 * margin)
            h = min(height - y, h + 2 * margin)
            
            # 裁剪图像
            cropped = img.crop((x, y, x + w, y + h))
            
            # 将裁剪的图像转换为PDF并添加到writer
            pdf_bytes = BytesIO()
            cropped.save(pdf_bytes, format='PDF')
            pdf_bytes.seek(0)
            temp_reader = PdfReader(pdf_bytes)
            pdf_writer.add_page(temp_reader.pages[0])
            
            if progress_callback:
                progress_callback(progress, f"添加第 {page_num + 1} 页的第 {idx + 1} 个回执单")

    # 保存合并后的PDF
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    with open(output_path, 'wb') as output_file:
        pdf_writer.write(output_file)
    
    if progress_callback:
        progress_callback(100, f"已保存合并后的PDF文件: {output_path}")

def main():
    try:
        # 设置输入和输出路径
        input_pdf = "./receipts.pdf"
        output_pdf = "./output_opencv/merged_receipts.pdf"
        
        # 处理所有页面
        process_pdf_with_opencv(input_pdf, output_pdf)
        print("\n处理完成！")
        
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 