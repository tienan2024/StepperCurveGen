import PyInstaller.__main__
import os

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

PyInstaller.__main__.run([
    'stepper_curve_generator.py',  # 主程序文件
    '--name=步进电机曲线生成器',  # 生成的exe名称
    '--windowed',  # 使用GUI模式
    '--onefile',  # 打包成单个exe文件
    '--icon=myicon.ico',  # 使用自定义图标
    '--clean',  # 清理临时文件
    '--noconfirm',  # 不询问确认
]) 