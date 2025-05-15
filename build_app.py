import os
import subprocess
import shutil

def create_executable():
    """创建单文件可执行程序"""
    print("开始打包应用...")
    
    # 应用程序名称
    app_name = "步进电机曲线生成器"
    
    # 清理之前的构建文件
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists(f"{app_name}.spec"):
        os.remove(f"{app_name}.spec")
    
    # 构建命令
    cmd = [
        "pyinstaller",
        "--name", app_name,
        "--windowed",  # 不显示控制台窗口
        "--onefile",   # 打包成单个文件
        "--icon=myicon.ico",  # 程序图标，请确保此文件存在
        "--add-data", "myicon.ico;.",  # 包含图标文件
        "--noconfirm",  # 不显示确认对话框
        "--clean",      # 清理临时文件
        "stepper_curve_generator.py"
    ]
    
    # 执行打包命令
    try:
        subprocess.run(cmd, check=True)
        print(f"应用程序成功打包为: dist/{app_name}.exe")
        print("你可以在dist文件夹中找到可执行文件。")
    except subprocess.CalledProcessError:
        print("打包失败。")
        
    # 创建readme文件到dist目录
    if os.path.exists("dist"):
        with open("dist/使用说明.txt", "w", encoding="utf-8") as f:
            f.write("步进电机曲线生成器\n")
            f.write("开发者: jzd\n\n")
            f.write("使用说明:\n")
            f.write("1. 启动应用程序\n")
            f.write("2. 选择曲线类型（线性、指数、S型、余弦、抛物线或自定义幂函数）\n")
            f.write("3. 设置点数、起始/终止值\n")
            f.write("4. 配置生效范围（可设置曲线只在部分步数中生效）\n") 
            f.write("5. 设置起始段和末尾段的点数（用于平滑过渡）\n")
            f.write("6. 对于自定义幂函数，可调整幂指数值\n")
            f.write("7. 点击生成曲线\n")
            f.write("8. 使用鼠标直接点击和拖动曲线上的点来修改值\n")
            f.write("9. 也可使用方向键和调整按钮精确修改\n")
            f.write("10. 导出C数组用于实际应用\n\n")
            f.write("曲线类型说明:\n")
            f.write("- 线性: 速度均匀变化，最基本的加减速曲线\n")
            f.write("- 指数: 速度指数级变化，初始加速和最终减速更快\n")
            f.write("- S型: 三次曲线，起始和结束更平滑，适合大多数场景\n")
            f.write("- 余弦: 基于余弦函数的平滑过渡，非常平滑的加减速\n")
            f.write("- 抛物线: 二次曲线，加减速度逐渐变化，中间段减速明显\n")
            f.write("- 自定义幂函数: 可自定义幂指数，精确控制加减速特性\n")

if __name__ == "__main__":
    create_executable() 