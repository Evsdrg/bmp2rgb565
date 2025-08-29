#  bmp2rgb565
一款基于Python、由AI生成的，用于将任意bmp转为RGB565或者其他格式，并以数组形式输出，以供单片机彩色显示屏使用的程序。

## 主要功能
将任意bmp图片转为RGB565，且可选择输出为16位数组或者8位数组，以适应不同的屏幕驱动。
还可以转为RGB332或者GRAY8灰度，并以8位数组模式输出。
输出的数组可以选择**小端序**或者**大端序**。


------------


## 使用方法

### 方法1：直接运行可执行文件（推荐）

1. **GUI模式**：双击 `dist/BMP_to_RGB565_Converter.exe` 启动图形界面
2. **命令行模式**：
   ```cmd
   BMP_to_RGB565_Converter.exe input.bmp output.h [little|big]
   ```

### 方法2：运行Python脚本

1. **安装依赖**：
   ```cmd
   pip install -r requirements.txt
   ```

2. **GUI模式**：
   ```cmd
   python bmp_to_rgb565_enhanced.py
   ```

3. **命令行模式**：
   ```cmd
   python bmp_to_rgb565_enhanced.py input.bmp output.h [format] [byte_order]
   ```
  format 可选: RGB565 (默认), RGB565_8BIT, RGB332, GRAY8

## 输出格式

生成的C语言数组格式（以16bitRGB565为例）：
```c
// BMP转RGB565数组
// 原始尺寸: 宽×高, 位深度
// 字节顺序: little-endian/big-endian
const uint16_t image_宽x高[像素总数] = {
    0xRGB5, 0xRGB5, 0xRGB5, ...
};
```



------------



#### 开源协议：MIT
允许自由使用、修改和分发，但请保留原始版权和许可信息。


------------



##### 感谢TRAE、Deepseek、Qwen、Claude帮我完成了这个程序
