import struct
import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
import threading

class BMPConverter:
    def __init__(self):
        self.supported_formats = [8, 16, 24, 32]
        self.output_formats = ['RGB565', 'RGB332', 'GRAY8', 'RGB565_8BIT']
        
    def detect_bmp_format(self, file_path):
        """自动检测BMP文件格式"""
        try:
            with open(file_path, 'rb') as f:
                # 读取BMP文件头
                bmp_header = f.read(14)
                if bmp_header[0:2] != b'BM':
                    return None, "不是有效的BMP文件"
                
                # 读取DIB头
                dib_header = f.read(40)
                width, height = struct.unpack('<II', dib_header[4:12])
                bpp = struct.unpack('<H', dib_header[14:16])[0]
                compression = struct.unpack('<I', dib_header[16:20])[0]
                
                info = {
                    'width': width,
                    'height': height,
                    'bpp': bpp,
                    'compression': compression,
                    'file_size': os.path.getsize(file_path)
                }
                
                return info, None
        except Exception as e:
            return None, f"读取文件错误: {str(e)}"
    
    def convert_pixel_to_rgb565(self, r, g, b, byte_order='little'):
        """将RGB像素转换为RGB565格式"""
        # 转换为RGB565
        r5 = (r * 31 + 127) // 255  # 8位红色转5位
        g6 = (g * 63 + 127) // 255  # 8位绿色转6位
        b5 = (b * 31 + 127) // 255  # 8位蓝色转5位
        rgb565 = (r5 << 11) | (g6 << 5) | b5
        
        # 处理字节顺序
        if byte_order == 'big':
            rgb565 = ((rgb565 & 0xFF) << 8) | (rgb565 >> 8)
        
        return rgb565
    
    def convert_pixel_to_rgb332(self, r, g, b, byte_order='little'):
        """将RGB像素转换为RGB332格式（8位）"""
        # 转换为RGB332: 3位红色，3位绿色，2位蓝色
        r3 = (r * 7 + 127) // 255   # 8位红色转3位
        g3 = (g * 7 + 127) // 255   # 8位绿色转3位
        b2 = (b * 3 + 127) // 255   # 8位蓝色转2位
        rgb332 = (r3 << 5) | (g3 << 2) | b2
        return rgb332
    
    def convert_pixel_to_grayscale8(self, r, g, b, byte_order='little'):
        """将RGB像素转换为8位灰度"""
        # 使用标准灰度转换公式
        gray = int(0.299 * r + 0.587 * g + 0.114 * b)
        return min(255, max(0, gray))
    
    def read_bmp_pixels(self, file_path, bmp_info):
        """读取BMP像素数据，支持多种格式"""
        width = bmp_info['width']
        height = bmp_info['height']
        bpp = bmp_info['bpp']
        
        pixels = []
        
        try:
            # 使用PIL库来处理复杂的BMP格式
            with Image.open(file_path) as img:
                # 转换为RGB模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 获取像素数据
                for y in range(height):
                    row = []
                    for x in range(width):
                        r, g, b = img.getpixel((x, y))
                        row.append((r, g, b))
                    pixels.append(row)
                
                return pixels, None
                
        except Exception as e:
            # 如果PIL失败，尝试手动解析
            return self.read_bmp_manually(file_path, bmp_info)
    
    def read_bmp_manually(self, file_path, bmp_info):
        """手动解析BMP文件"""
        width = bmp_info['width']
        height = bmp_info['height']
        bpp = bmp_info['bpp']
        
        try:
            with open(file_path, 'rb') as f:
                # 跳过文件头和DIB头
                f.seek(54)
                
                # 计算每行字节数
                bytes_per_pixel = bpp // 8
                row_size = (width * bytes_per_pixel + 3) & ~3
                padding = row_size - width * bytes_per_pixel
                
                pixels = []
                
                for y in range(height):
                    row = []
                    for x in range(width):
                        if bpp == 24:
                            # 24位BMP: BGR顺序
                            b, g, r = struct.unpack('BBB', f.read(3))
                        elif bpp == 32:
                            # 32位BMP: BGRA顺序
                            b, g, r, a = struct.unpack('BBBB', f.read(4))
                        elif bpp == 16:
                            # 16位BMP: 通常是RGB555或RGB565
                            pixel_data = struct.unpack('<H', f.read(2))[0]
                            # 假设是RGB555格式
                            r = ((pixel_data >> 10) & 0x1F) * 255 // 31
                            g = ((pixel_data >> 5) & 0x1F) * 255 // 31
                            b = (pixel_data & 0x1F) * 255 // 31
                        elif bpp == 8:
                            # 8位BMP需要调色板，这里简化处理
                            gray = struct.unpack('B', f.read(1))[0]
                            r = g = b = gray
                        else:
                            return None, f"不支持的位深度: {bpp}"
                        
                        row.append((r, g, b))
                    
                    # 跳过填充字节
                    f.read(padding)
                    # BMP从下到上存储，需要反转
                    pixels.insert(0, row)
                
                return pixels, None
                
        except Exception as e:
            return None, f"手动解析失败: {str(e)}"
    
    def convert_bmp_to_array(self, input_file, output_file, output_format='RGB565', byte_order='little', progress_callback=None):
        """将BMP文件转换为指定格式的数组"""
        # 检测BMP格式
        bmp_info, error = self.detect_bmp_format(input_file)
        if error:
            return False, error
        
        width = bmp_info['width']
        height = bmp_info['height']
        bpp = bmp_info['bpp']
        
        if progress_callback:
            progress_callback(f"检测到 {width}×{height} {bpp}位 BMP文件，输出格式: {output_format}")
        
        # 读取像素数据
        pixels, error = self.read_bmp_pixels(input_file, bmp_info)
        if error:
            return False, error
        
        if progress_callback:
            progress_callback("开始转换像素数据...")
        
        # 转换并写入输出文件
        try:
            with open(output_file, 'w', encoding='utf-8') as out_f:
                # 写入数组声明
                array_name = f"image_{width}x{height}"
                if output_format == 'RGB565':
                    data_type = "uint16_t"
                    out_f.write(f"// BMP转RGB565数组\n")
                    out_f.write(f"// 字节顺序: {byte_order}-endian\n")
                elif output_format == 'RGB332':
                    data_type = "uint8_t"
                    out_f.write(f"// BMP转RGB332数组\n")
                    out_f.write(f"// 字节顺序: {byte_order}-endian\n")
                elif output_format == 'GRAY8':
                    data_type = "uint8_t"
                    out_f.write(f"// BMP转8位灰度数组\n")
                    out_f.write(f"// 字节顺序: {byte_order}-endian\n")
                elif output_format == 'RGB565_8BIT':
                    data_type = "unsigned char"
                    out_f.write(f"// BMP转RGB565 8位字节数组\n")
                    out_f.write(f"// 字节顺序: {byte_order}-endian\n")
                
                out_f.write(f"// 原始尺寸: {width}×{height}, {bpp}位\n")
                out_f.write(f"// 输出格式: {output_format}\n")
                
                # 计算数组大小
                if output_format == 'RGB565_8BIT':
                    array_size = width * height * 2  # 每个像素2字节
                else:
                    array_size = width * height
                
                out_f.write(f"const {data_type} {array_name}[{array_size}] = {{\n")
                
                total_pixels = width * height
                processed = 0
                
                for y, row in enumerate(pixels):
                    for x, (r, g, b) in enumerate(row):
                        # 根据输出格式转换像素
                        if output_format == 'RGB565':
                            pixel_value = self.convert_pixel_to_rgb565(r, g, b, byte_order)
                            format_str = f"0x{pixel_value:04X}"
                        elif output_format == 'RGB332':
                            pixel_value = self.convert_pixel_to_rgb332(r, g, b, byte_order)
                            format_str = f"0x{pixel_value:02X}"
                        elif output_format == 'GRAY8':
                            pixel_value = self.convert_pixel_to_grayscale8(r, g, b, byte_order)
                            format_str = f"0x{pixel_value:02X}"
                        elif output_format == 'RGB565_8BIT':
                            pixel_value = self.convert_pixel_to_rgb565(r, g, b, byte_order)
                            # 拆分为高低字节
                            if byte_order == 'little':
                                low_byte = pixel_value & 0xFF
                                high_byte = (pixel_value >> 8) & 0xFF
                                format_str = f"0X{high_byte:02X},0X{low_byte:02X}"
                            else:
                                high_byte = (pixel_value >> 8) & 0xFF
                                low_byte = pixel_value & 0xFF
                                format_str = f"0X{high_byte:02X},0X{low_byte:02X}"
                        
                        # 格式化输出
                        if output_format == 'RGB565_8BIT':
                            # 8位字节数组格式，每行8个字节（4个像素）
                            if x % 4 == 0:
                                out_f.write("    ")
                            
                            out_f.write(format_str)
                            
                            # 添加逗号和换行
                            if y != height - 1 or x != width - 1:
                                out_f.write(",")
                            
                            if x % 4 == 3:
                                out_f.write("\n")
                        else:
                            # 其他格式保持原有逻辑
                            if x % 16 == 0:
                                out_f.write("    ")
                            
                            out_f.write(format_str)
                            
                            # 添加逗号和换行
                            if y != height - 1 or x != width - 1:
                                out_f.write(", ")
                            
                            if x % 16 == 15:
                                out_f.write("\n")
                        
                        processed += 1
                        if progress_callback and processed % 1000 == 0:
                            progress = int((processed / total_pixels) * 100)
                            progress_callback(f"转换进度: {progress}%")
                
                # 处理最后一行
                if width % 16 != 0:
                    out_f.write("\n")
                
                out_f.write("};\n")
            
            if progress_callback:
                progress_callback("转换完成！")
            
            return True, f"成功转换 {width}×{height} 图像到 {output_file}"
            
        except Exception as e:
            return False, f"写入文件错误: {str(e)}"

class BMPConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("BMP转RGB565转换器")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        # 设置窗口最小尺寸，防止界面元素被遮挡
        self.root.minsize(600, 500)
        
        self.converter = BMPConverter()
        self.input_file = ""
        self.output_file = ""
        
        self.setup_ui()
    
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)  # 让文件信息栏可以垂直扩展
        
        # 输入文件选择
        ttk.Label(main_frame, text="输入BMP文件:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.input_var, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="浏览", command=self.browse_input).grid(row=0, column=2, padx=5)
        
        # 输出文件选择
        ttk.Label(main_frame, text="输出文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.output_var, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="浏览", command=self.browse_output).grid(row=1, column=2, padx=5)
        
        # 输出格式选择
        ttk.Label(main_frame, text="输出格式:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.output_format_var = tk.StringVar(value="RGB565")
        self.display_format_var = tk.StringVar(value="RGB565 (16位)")
        format_options = [
            ("RGB565 (16位)", "RGB565"),
            ("RGB565 (8位字节)", "RGB565_8BIT"),
            ("RGB332 (8位)", "RGB332"),
            ("灰度 (8位)", "GRAY8")
        ]
        self.format_combobox = ttk.Combobox(main_frame, textvariable=self.display_format_var, 
                                           values=[option[0] for option in format_options], 
                                           state="readonly", width=20)
        self.format_combobox.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        self.format_combobox.bind('<<ComboboxSelected>>', self.on_format_change)
        
        # 创建格式映射字典
        self.format_mapping = {option[0]: option[1] for option in format_options}
        self.reverse_format_mapping = {option[1]: option[0] for option in format_options}
        self.format_combobox.set("RGB565 (16位)")
        
        # 字节顺序选择
        ttk.Label(main_frame, text="字节顺序:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.byte_order_var = tk.StringVar(value="little")
        self.byte_order_frame = ttk.Frame(main_frame)
        self.byte_order_frame.grid(row=3, column=1, sticky=tk.W, pady=5)
        self.byte_order_little = ttk.Radiobutton(self.byte_order_frame, text="小端序 (Little)", variable=self.byte_order_var, value="little")
        self.byte_order_little.pack(side=tk.LEFT)
        self.byte_order_big = ttk.Radiobutton(self.byte_order_frame, text="大端序 (Big)", variable=self.byte_order_var, value="big")
        self.byte_order_big.pack(side=tk.LEFT, padx=10)
        
        # 文件信息显示
        info_frame = ttk.LabelFrame(main_frame, text="文件信息", padding="5")
        info_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)  # 让文本框可以垂直扩展
        
        self.info_text = tk.Text(info_frame, height=6, width=70)
        info_scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scrollbar.set)
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        info_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 转换按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10)
        ttk.Button(button_frame, text="开始转换", command=self.start_conversion).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清除信息", command=self.clear_info).pack(side=tk.LEFT, padx=5)
        
        # 进度条
        self.progress_var = tk.StringVar(value="就绪")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=6, column=0, columnspan=3, pady=5)
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # 开源协议信息
        license_frame = ttk.Frame(main_frame)
        license_frame.grid(row=8, column=0, columnspan=3, pady=5)
        license_text = "本软件采用 MIT 开源许可证发布，允许任何人自由使用、修改和分发，前提是保留原始的版权声明和许可声明。"
        ttk.Label(license_frame, text=license_text, font=('Arial', 8), foreground='gray').pack()
    
    def on_format_change(self, event=None):
        """当输出格式改变时的处理"""
        # 获取实际的格式值
        display_format = self.format_combobox.get()
        actual_format = self.format_mapping.get(display_format, "RGB565")
        self.output_format_var.set(actual_format)
        
        # 所有格式都支持字节顺序选择
        self.byte_order_little.config(state='normal')
        self.byte_order_big.config(state='normal')
    
    def browse_input(self):
        filename = filedialog.askopenfilename(
            title="选择BMP文件",
            filetypes=[("BMP文件", "*.bmp"), ("所有文件", "*.*")]
        )
        if filename:
            self.input_var.set(filename)
            self.analyze_input_file(filename)
    
    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            title="保存为",
            defaultextension=".h",
            filetypes=[("C头文件", "*.h"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            self.output_var.set(filename)
    
    def analyze_input_file(self, filename):
        """分析输入文件并显示信息"""
        info, error = self.converter.detect_bmp_format(filename)
        
        self.info_text.delete(1.0, tk.END)
        
        if error:
            self.info_text.insert(tk.END, f"错误: {error}\n")
        else:
            self.info_text.insert(tk.END, f"文件路径: {filename}\n")
            self.info_text.insert(tk.END, f"图像尺寸: {info['width']} × {info['height']}\n")
            self.info_text.insert(tk.END, f"位深度: {info['bpp']} 位\n")
            self.info_text.insert(tk.END, f"压缩方式: {info['compression']}\n")
            self.info_text.insert(tk.END, f"文件大小: {info['file_size']:,} 字节\n")
            self.info_text.insert(tk.END, f"像素总数: {info['width'] * info['height']:,}\n")
            
            # 自动设置输出文件名
            if not self.output_var.get():
                base_name = os.path.splitext(os.path.basename(filename))[0]
                format_suffix = self.output_format_var.get().lower()
                output_name = f"{base_name}_{format_suffix}.h"
                output_path = os.path.join(os.path.dirname(filename), output_name)
                self.output_var.set(output_path)
    
    def clear_info(self):
        self.info_text.delete(1.0, tk.END)
        self.progress_var.set("就绪")
    
    def update_progress(self, message):
        """更新进度信息"""
        self.progress_var.set(message)
        self.root.update_idletasks()
    
    def start_conversion(self):
        """开始转换过程"""
        input_file = self.input_var.get().strip()
        output_file = self.output_var.get().strip()
        
        if not input_file:
            messagebox.showerror("错误", "请选择输入文件")
            return
        
        if not output_file:
            messagebox.showerror("错误", "请指定输出文件")
            return
        
        if not os.path.exists(input_file):
            messagebox.showerror("错误", "输入文件不存在")
            return
        
        # 在新线程中执行转换
        self.progress_bar.start()
        thread = threading.Thread(target=self.conversion_thread, args=(input_file, output_file))
        thread.daemon = True
        thread.start()
    
    def conversion_thread(self, input_file, output_file):
        """转换线程"""
        try:
            output_format = self.output_format_var.get()
            # 直接从单选按钮获取字节序值
            byte_order = self.byte_order_var.get()
            success, message = self.converter.convert_bmp_to_array(
                input_file, output_file, output_format, byte_order, self.update_progress
            )
            
            # 在主线程中更新UI
            self.root.after(0, self.conversion_complete, success, message)
            
        except Exception as e:
            self.root.after(0, self.conversion_complete, False, f"转换过程中发生错误: {str(e)}")
    
    def conversion_complete(self, success, message):
        """转换完成回调"""
        self.progress_bar.stop()
        
        if success:
            messagebox.showinfo("成功", message)
            self.progress_var.set("转换完成")
        else:
            messagebox.showerror("错误", message)
            self.progress_var.set("转换失败")

def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 命令行模式
        if len(sys.argv) < 3:
            print("用法: python bmp_to_rgb565_enhanced.py input.bmp output.h [format] [byte_order]")
            print("format 可选: RGB565 (默认), RGB565_8BIT, RGB332, GRAY8")
            print("byte_order 可选: little (默认) 或 big (所有格式均支持字节序选择)")
            sys.exit(1)
        
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        output_format = 'RGB565'
        byte_order = 'little'
        
        if len(sys.argv) > 3:
            output_format = sys.argv[3]
            if output_format not in ['RGB565', 'RGB565_8BIT', 'RGB332', 'GRAY8']:
                print("错误: format 必须是 'RGB565', 'RGB565_8BIT', 'RGB332' 或 'GRAY8'")
                sys.exit(1)
        
        if len(sys.argv) > 4:
            byte_order = sys.argv[4].lower()
            if byte_order not in ['little', 'big']:
                print("错误: byte_order 必须是 'little' 或 'big'")
                sys.exit(1)
        
        if not os.path.exists(input_file):
            print(f"错误: 输入文件 '{input_file}' 不存在")
            sys.exit(1)
        
        converter = BMPConverter()
        success, message = converter.convert_bmp_to_array(input_file, output_file, output_format, byte_order)
        
        if success:
            print(message)
            sys.exit(0)
        else:
            print(f"错误: {message}")
            sys.exit(1)
    else:
        # GUI模式
        root = tk.Tk()
        app = BMPConverterGUI(root)
        root.mainloop()

if __name__ == "__main__":
    main()