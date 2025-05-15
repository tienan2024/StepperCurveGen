import sys
import re
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                           QComboBox, QSpinBox, QGroupBox, QMessageBox, QDoubleSpinBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
from matplotlib.widgets import PolygonSelector

# 设置matplotlib支持中文显示
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
matplotlib.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

class StepperCurveGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("by jzd")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置应用程序图标
        self.setWindowIcon(QIcon("myicon.ico"))
        
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 创建主布局
        layout = QHBoxLayout()
        main_widget.setLayout(layout)
        
        # 配置matplotlib参数
        matplotlib.rcParams['interactive'] = True
        matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
        matplotlib.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
        matplotlib.rcParams['toolbar'] = 'None'  # 禁用工具栏
        matplotlib.rcParams['path.simplify'] = True  # 简化路径以提高性能
        matplotlib.rcParams['path.simplify_threshold'] = 1.0  # 最大化简化
        
        # 创建figure和canvas
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setFocusPolicy(Qt.StrongFocus)  # 强制获取焦点
        self.canvas.setFocus()  # 设置默认焦点在画布上
        # 确保图表响应鼠标事件
        self.canvas.setMouseTracking(True)
        self.ax = self.figure.add_subplot(111)
        
        # 左侧控制面板
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel, stretch=1)
        
        # 右侧图表面板
        plot_panel = self.create_plot_panel()
        layout.addWidget(plot_panel, stretch=2)
        
        # 初始化数据
        self.current_array = []
        
        # 用于拖拽修改的变量
        self.dragging = False
        self.selected_point = None
        self.initial_y = None  # 初始化initial_y属性
        self.scatter_plot = None
        self.line_plot = None
        self.highlight_point = None
        self.velocity_line = None
        self.cursor_annotation = None  # 鼠标位置的注释
        self.point_info_text = None  # 选中点的信息文本
        
        # 连接鼠标事件 (增加事件监听能力)
        self.cidpress = self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.cidrelease = self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.cidmotion = self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.cidpick = self.canvas.mpl_connect('pick_event', self.on_pick)
        
        # 添加键盘事件支持
        self.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        # 状态标签
        self.status_label = QLabel("准备就绪")
        self.statusBar().addWidget(self.status_label)
        
        # 脉冲时间信息标签
        self.pulse_info_label = QLabel("脉冲时间: --")
        self.pulse_info_label.setStyleSheet("color: blue; font-weight: bold;")
        self.statusBar().addPermanentWidget(self.pulse_info_label)
        
    def create_control_panel(self):
        panel = QGroupBox("控制面板")
        layout = QVBoxLayout()
        
        # 数组输入区域
        input_group = QGroupBox("数组输入")
        input_layout = QVBoxLayout()
        self.array_input = QTextEdit()
        self.array_input.setPlaceholderText("在此粘贴C数组...")
        input_layout.addWidget(self.array_input)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 曲线生成参数
        param_group = QGroupBox("曲线参数")
        param_layout = QVBoxLayout()
        
        # 曲线类型选择
        curve_type_layout = QHBoxLayout()
        curve_type_layout.addWidget(QLabel("曲线类型:"))
        self.curve_type = QComboBox()
        self.curve_type.addItems(["线性", "指数", "S型", "余弦", "抛物线", "自定义幂函数"])
        curve_type_layout.addWidget(self.curve_type)
        param_layout.addLayout(curve_type_layout)
        
        # 点数设置
        points_layout = QHBoxLayout()
        points_layout.addWidget(QLabel("点数:"))
        self.points_spin = QSpinBox()
        self.points_spin.setRange(10, 500)
        self.points_spin.setValue(98)
        points_layout.addWidget(self.points_spin)
        param_layout.addLayout(points_layout)
        
        # 起始值和终止值
        start_end_layout = QHBoxLayout()
        start_end_layout.addWidget(QLabel("起始值:"))
        self.start_value = QSpinBox()
        self.start_value.setRange(1, 1000)
        self.start_value.setValue(93)
        start_end_layout.addWidget(self.start_value)
        
        start_end_layout.addWidget(QLabel("终止值:"))
        self.end_value = QSpinBox()
        self.end_value.setRange(1, 1000)
        self.end_value.setValue(8)
        start_end_layout.addWidget(self.end_value)
        param_layout.addLayout(start_end_layout)
        
        # 添加生效范围设置
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("生效范围:"))
        self.range_start = QSpinBox()
        self.range_start.setRange(0, 100)
        self.range_start.setValue(0)
        self.range_start.setSuffix("%")
        range_layout.addWidget(self.range_start)
        
        range_layout.addWidget(QLabel("至"))
        self.range_end = QSpinBox()
        self.range_end.setRange(0, 100)
        self.range_end.setValue(100)
        self.range_end.setSuffix("%")
        range_layout.addWidget(self.range_end)
        param_layout.addLayout(range_layout)
        
        # 添加起始大小和末尾大小设置
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("起始段点数:"))
        self.start_size = QSpinBox()
        self.start_size.setRange(1, 100)
        self.start_size.setValue(10)
        size_layout.addWidget(self.start_size)
        
        size_layout.addWidget(QLabel("末尾段点数:"))
        self.end_size = QSpinBox()
        self.end_size.setRange(1, 100)
        self.end_size.setValue(10)
        size_layout.addWidget(self.end_size)
        param_layout.addLayout(size_layout)
        
        # 添加幂函数指数设置
        power_layout = QHBoxLayout()
        power_layout.addWidget(QLabel("幂函数指数:"))
        self.power_value = QDoubleSpinBox()
        self.power_value.setRange(0.1, 10.0)
        self.power_value.setValue(2.0)
        self.power_value.setSingleStep(0.1)
        power_layout.addWidget(self.power_value)
        param_layout.addLayout(power_layout)
        
        # 添加参数说明提示
        help_text = """
<b>曲线类型说明：</b><br>
- <b>线性</b>：速度均匀变化<br>
- <b>指数</b>：速度指数级变化，加减速更快<br>
- <b>S型</b>：三次曲线，起始和结束更平滑<br>
- <b>余弦</b>：基于余弦函数的平滑过渡<br>
- <b>抛物线</b>：二次曲线，加减速度逐渐变化<br>
- <b>自定义幂函数</b>：自定义幂指数的变化曲线<br>
<br>
<b>生效范围</b>：可以设置曲线只在部分步数中生效<br>
<b>起始/末尾段点数</b>：设置起始和末尾部分的平滑过渡点数
"""
        help_label = QLabel(help_text)
        help_label.setStyleSheet("background-color: #f0f0f0; padding: 5px; border-radius: 3px;")
        param_layout.addWidget(help_label)
        
        param_group.setLayout(param_layout)
        layout.addWidget(param_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.import_btn = QPushButton("导入数组")
        self.generate_btn = QPushButton("生成曲线")
        self.export_btn = QPushButton("导出C数组")
        
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.export_btn)
        layout.addLayout(button_layout)
        
        # 拖拽提示
        drag_tip = QLabel("提示: 点击曲线上的蓝色点并上下拖动修改值")
        drag_tip.setStyleSheet("color: blue; font-weight: bold;")
        layout.addWidget(drag_tip)
        
        # 拖拽状态
        self.drag_status = QLabel("未选中任何点")
        self.drag_status.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.drag_status)
        
        # 耗时显示
        self.time_cost_label = QLabel("总耗时: 0 ms")
        layout.addWidget(self.time_cost_label)
        
        # 连接信号
        self.import_btn.clicked.connect(self.import_array)
        self.generate_btn.clicked.connect(self.generate_curve)
        self.export_btn.clicked.connect(self.export_array)
        
        # 设置部分控件的显示/隐藏逻辑
        self.curve_type.currentTextChanged.connect(self.update_control_visibility)
        
        panel.setLayout(layout)
        return panel
        
    def create_plot_panel(self):
        panel = QGroupBox("曲线显示")
        layout = QVBoxLayout()
        
        # 使用已创建的matplotlib画布
        layout.addWidget(self.canvas)
        
        # 添加操作提示标签
        tip_label = QLabel("◆ 如果点击散点无效，请直接点击曲线上方并使用下方按钮模拟点击")
        tip_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(tip_label)
        
        # 添加键盘操作提示
        keyboard_tip = QLabel("◆ 键盘操作: 选中点后可用↑↓键调整值，用←→键切换点")
        keyboard_tip.setStyleSheet("color: blue; font-weight: bold;")
        layout.addWidget(keyboard_tip)
        
        # 点信息显示区域
        self.point_info_area = QLabel("选中点信息显示区域")
        self.point_info_area.setStyleSheet("background-color: lightyellow; padding: 5px; border: 1px solid gray;")
        self.point_info_area.setMinimumHeight(50)
        self.point_info_area.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.point_info_area)
        
        # 添加直接点击按钮，用于模拟点击功能
        click_btn_layout = QHBoxLayout()
        
        self.x_pos_label = QLabel("X坐标:")
        self.x_pos_spin = QSpinBox()
        self.x_pos_spin.setRange(0, 100)
        self.x_pos_spin.setValue(0)
        
        self.y_value_label = QLabel("新值:")
        self.y_value_spin = QSpinBox()
        self.y_value_spin.setRange(6, 98)  # 调整范围为6-98
        self.y_value_spin.setValue(50)
        
        self.click_btn = QPushButton("选中点")
        self.click_btn.clicked.connect(self.simulate_click)
        
        self.modify_btn = QPushButton("修改值")
        self.modify_btn.clicked.connect(self.modify_point_value)
        
        click_btn_layout.addWidget(self.x_pos_label)
        click_btn_layout.addWidget(self.x_pos_spin)
        click_btn_layout.addWidget(self.y_value_label)
        click_btn_layout.addWidget(self.y_value_spin)
        click_btn_layout.addWidget(self.click_btn)
        click_btn_layout.addWidget(self.modify_btn)
        
        layout.addLayout(click_btn_layout)
        
        # 添加增量调整按钮
        adjust_layout = QHBoxLayout()
        
        adjust_label = QLabel("增量调整:")
        
        self.decrease_btn = QPushButton("-")
        self.decrease_btn.clicked.connect(lambda: self.adjust_value(-1))
        
        self.fine_decrease_btn = QPushButton("-0.1")
        self.fine_decrease_btn.clicked.connect(lambda: self.adjust_value(-0.1))
        
        self.fine_increase_btn = QPushButton("+0.1")
        self.fine_increase_btn.clicked.connect(lambda: self.adjust_value(0.1))
        
        self.increase_btn = QPushButton("+")
        self.increase_btn.clicked.connect(lambda: self.adjust_value(1))
        
        adjust_layout.addWidget(adjust_label)
        adjust_layout.addWidget(self.decrease_btn)
        adjust_layout.addWidget(self.fine_decrease_btn)
        adjust_layout.addWidget(self.fine_increase_btn)
        adjust_layout.addWidget(self.increase_btn)
        
        layout.addLayout(adjust_layout)
        
        panel.setLayout(layout)
        return panel
        
    def parse_c_array(self, text):
        """解析C数组文本为Python列表"""
        nums = re.findall(r'\{([^\}]*)\}', text)
        if not nums:
            return []
        try:
            arr = [int(x.strip()) for x in nums[0].split(',') if x.strip().isdigit()]
            return arr
        except ValueError:
            return []
            
    def import_array(self):
        """导入数组并显示曲线"""
        text = self.array_input.toPlainText()
        self.current_array = self.parse_c_array(text)
        if not self.current_array:
            QMessageBox.warning(self, "警告", "无法解析数组，请检查格式！")
            return
            
        # 清除选择状态，避免重影
        self.reset_selection_state()
        self.plot_array(self.current_array)
        
    def generate_curve(self):
        """根据参数生成曲线"""
        curve_type = self.curve_type.currentText()
        n_points = self.points_spin.value()
        start = self.start_value.value()
        end = self.end_value.value()
        
        # 获取生效范围
        range_start_percent = self.range_start.value() / 100
        range_end_percent = self.range_end.value() / 100
        
        # 获取起始段和末尾段点数
        start_size = self.start_size.value()
        end_size = self.end_size.value()
        
        # 创建全长数组
        full_array = np.zeros(n_points, dtype=int)
        
        # 计算实际生效范围的点数
        start_idx = int(n_points * range_start_percent)
        end_idx = int(n_points * range_end_percent)
        effect_points = end_idx - start_idx
        
        # 确保起始段和末尾段点数不超过生效范围
        start_size = min(start_size, effect_points // 3)
        end_size = min(end_size, effect_points // 3)
        
        # 根据曲线类型生成中间部分曲线
        mid_points = effect_points - start_size - end_size
        
        # 不同曲线类型的生成方法
        if curve_type == "线性":
            # 线性变化
            effect_curve = np.linspace(start, end, effect_points)
        elif curve_type == "指数":
            # 指数变化 - 防止log(0)错误
            start_val = max(1, start)
            end_val = max(1, end)
            effect_curve = np.exp(np.linspace(np.log(start_val), np.log(end_val), effect_points))
        elif curve_type == "S型":
            # S型曲线 (三次多项式)
            t = np.linspace(0, 1, effect_points)
            effect_curve = start + (end - start) * (3*t**2 - 2*t**3)
        elif curve_type == "余弦":
            # 余弦变化
            t = np.linspace(0, 1, effect_points)
            effect_curve = start + (end - start) * (1 - np.cos(t * np.pi)) / 2
        elif curve_type == "抛物线":
            # 抛物线变化
            t = np.linspace(0, 1, effect_points)
            effect_curve = start + (end - start) * t**2
        elif curve_type == "自定义幂函数":
            # 幂函数变化
            power = self.power_value.value()
            t = np.linspace(0, 1, effect_points)
            if start >= end:
                effect_curve = start - (start - end) * t**power
            else:
                effect_curve = start + (end - start) * t**power
        else:
            # 默认线性
            effect_curve = np.linspace(start, end, effect_points)
        
        # 如果需要处理起始段和末尾段的特殊平滑
        if start_size > 0 or end_size > 0:
            # 提取主体曲线的起始值和结束值
            curve_start_val = effect_curve[0]
            curve_end_val = effect_curve[-1]
            
            # 重新生成曲线，考虑起始段和末尾段
            if start_size > 0:
                # 起始段使用S型过渡
                start_t = np.linspace(0, 1, start_size)
                start_curve = start + (curve_start_val - start) * (3*start_t**2 - 2*start_t**3)
                effect_curve[:start_size] = start_curve
                
            if end_size > 0:
                # 末尾段使用S型过渡
                end_t = np.linspace(0, 1, end_size)
                end_curve = curve_end_val + (end - curve_end_val) * (3*end_t**2 - 2*end_t**3)
                effect_curve[-end_size:] = end_curve
        
        # 曲线插入到整体数组中
        full_array[start_idx:end_idx] = effect_curve.astype(int)
        
        # 处理未覆盖的部分
        if start_idx > 0:
            # 起始段之前保持起始值
            full_array[:start_idx] = start
        
        if end_idx < n_points:
            # 末尾段之后保持终止值
            full_array[end_idx:] = end
        
        self.current_array = full_array.tolist()
            
        # 清除选择状态，避免重影
        self.reset_selection_state()
        self.plot_array(self.current_array)
    
    def on_mouse_move(self, event):
        """鼠标移动事件处理"""
        # 首先更新鼠标位置信息
        if event.inaxes == self.ax and len(self.current_array) > 0:
            # 当鼠标在图表区域内时，显示当前位置的脉冲时间
            x_pos = int(round(event.xdata))
            
            # 将Y轴坐标限制在0-100范围内
            y_data = event.ydata
            # 将Y坐标除以3，使得鼠标可以在更大范围内移动
            y_data = y_data / 3
            
            y_pos = int(round(y_data))
            
            # 确保在有效范围内
            if 0 <= x_pos < len(self.current_array):
                # 更新脉冲时间信息
                pulse_time = y_pos  # 脉冲时间直接对应Y坐标值
                self.pulse_info_label.setText(f"当前位置: X={x_pos}, Y={y_pos} (脉冲时间: {pulse_time}μs)")
                
                # 如果有对应角速度，也显示
                if pulse_time > 0:
                    step_angle = 1.8  # 度
                    angular_velocity = step_angle / (pulse_time/1000)  # 度/秒
                    self.pulse_info_label.setText(f"当前位置: X={x_pos}, Y={y_pos} (脉冲时间: {pulse_time}μs, 角速度: {angular_velocity:.2f}°/s)")
        
        # 如果没有选中点或者没有在拖动，则不继续处理拖动逻辑
        if not self.dragging or self.selected_point is None:
            return
            
        # 添加调试信息
        debug_info = f"拖动中: 坐标({event.x}, {event.y})"
        
        # 检查鼠标位置是否有有效坐标
        if event.xdata is None or event.ydata is None:
            self.status_label.setText(f"{debug_info} - 拖动位置缺少坐标数据")
            return
            
        # 添加数据坐标调试信息
        debug_info += f" 数据({event.xdata:.1f}, {event.ydata:.1f})"
        self.status_label.setText(debug_info)
        
        # 获取新的y值 - 将点直接移动到鼠标Y位置
        # 首先确保Y坐标在图表的有效范围内（0-100）
        y_data = event.ydata
        # 将Y坐标除以3，使得鼠标可以在更大范围内移动
        y_data = y_data / 3
            
        # 四舍五入到整数值
        new_y = int(round(y_data))
        
        # 再限制在应用程序要求的6-98范围内
        new_y = max(6, min(98, new_y))
        
        idx = self.selected_point
        
        # 直接赋值鼠标对应的Y值
        old_value = self.current_array[idx]
        self.current_array[idx] = new_y
        
        # 更新状态显示
        status_text = f"移动点: #{idx} 值为 {new_y} (鼠标Y={y_data:.1f})"
        self.status_label.setText(status_text)
        self.drag_status.setText(status_text)
        
        # 更新Y值输入框以匹配当前值
        if hasattr(self, 'y_value_spin'):
            self.y_value_spin.setValue(new_y)
        
        # 更新选中点信息
        self.update_point_info(idx, new_y)
        
        # 直接更新曲线点位置
        self.update_plot_for_drag(idx, new_y)
    
    def on_mouse_press(self, event):
        """鼠标按下事件处理"""
        # 添加更多调试信息
        debug_info = f"点击坐标: 屏幕({event.x}, {event.y})"
        self.status_label.setText(debug_info)
        
        # 检查点击是否在任何坐标轴上
        if event.inaxes is None:
            self.drag_status.setText(f"{debug_info} - 点击位置不在图表区域内")
            self.drag_status.setStyleSheet("color: red; font-weight: bold;")
            return
            
        # 添加数据坐标调试信息
        debug_info += f" 数据({event.xdata:.1f}, {event.ydata:.1f})"
        self.status_label.setText(debug_info)
            
        # 检查是否有数据可供选择
        if len(self.current_array) == 0:
            self.drag_status.setText(f"{debug_info} - 无数据")
            return
            
        # 直接根据x坐标选择最近的点
        if event.xdata is not None:
            # 将X坐标四舍五入到最近的整数
            x_coord = int(round(event.xdata))
            
            # 确保x坐标在有效范围内
            if 0 <= x_coord < len(self.current_array):
                self.selected_point = x_coord
                self.dragging = True
                
                # 获取当前Y值作为初始值
                self.initial_y = self.current_array[x_coord]
                
                # 更新Y值输入框以匹配当前值
                if hasattr(self, 'y_value_spin'):
                    self.y_value_spin.setValue(self.initial_y)
                
                # 直接将点移动到鼠标位置的Y坐标
                # 首先确保Y坐标在图表的有效范围内（0-100）
                y_data = event.ydata
                # 将Y坐标除以3，使得鼠标可以在更大范围内移动
                y_data = y_data / 3
                    
                # 四舍五入到整数值
                new_y = int(round(y_data))
                
                # 再限制在应用程序要求的6-98范围内
                new_y = max(6, min(98, new_y))
                
                self.current_array[x_coord] = new_y
                status_text = f"选中并直接移动点 #{x_coord} 至Y={new_y}"
                # 更新点的值
                self.initial_y = new_y  # 更新初始值
                
                self.status_label.setText(status_text)
                self.drag_status.setText(status_text)
                self.drag_status.setStyleSheet("color: green; font-weight: bold;")
                
                # 更新X坐标输入框
                if hasattr(self, 'x_pos_spin'):
                    self.x_pos_spin.setValue(x_coord)
                
                # 更新选中点信息显示
                self.update_point_info(x_coord, self.current_array[x_coord])
                
                # 更新图形
                self.plot_array(self.current_array)
                return True
            else:
                self.drag_status.setText(f"{debug_info} - X坐标 {x_coord} 超出范围 (0-{len(self.current_array)-1})")
                self.drag_status.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.drag_status.setText(f"{debug_info} - X坐标未定义")
            self.drag_status.setStyleSheet("color: red; font-weight: bold;")
            
        return False
    
    def on_mouse_release(self, event):
        """鼠标释放事件处理"""
        if self.dragging and self.selected_point is not None:
            idx = self.selected_point
            status_text = f"修改完成: 点 #{idx} 的值从 {self.initial_y} 变为 {self.current_array[idx]}"
            self.status_label.setText(status_text)
            self.drag_status.setText(status_text)
            self.drag_status.setStyleSheet("color: blue; font-weight: bold;")
            
            # 更新选中点信息，保持选中状态
            self.update_point_info(idx, self.current_array[idx])
            
            # 结束拖动状态，但保持选中状态
            self.dragging = False
            
            # 更新图形，保持高亮
            self.plot_array(self.current_array)
    
    def on_pick(self, event):
        """点击选择事件处理"""
        # 添加调试信息
        debug_info = f"拾取事件: 类型={type(event.artist).__name__}"
        self.status_label.setText(debug_info)
        
        try:
            # 被选中的点
            if event.artist == self.scatter_plot:
                # 获取被拾取的点的索引
                ind = event.ind
                if len(ind) > 0:
                    # 取第一个点的索引
                    x_coord = ind[0]
                    
                    # 获取鼠标坐标
                    mouse_event = event.mouseevent
                    has_mouse_y = hasattr(mouse_event, 'ydata') and mouse_event.ydata is not None
                    
                    # 确保坐标有效
                    if 0 <= x_coord < len(self.current_array):
                        self.selected_point = x_coord
                        self.dragging = True
                        
                        # 记录初始y值
                        self.initial_y = self.current_array[x_coord]
                        
                        # 更新Y值输入框以匹配当前值
                        if hasattr(self, 'y_value_spin'):
                            self.y_value_spin.setValue(self.initial_y)
                        
                        # 更新X坐标输入框
                        if hasattr(self, 'x_pos_spin'):
                            self.x_pos_spin.setValue(x_coord)
                        
                        # 直接将点移动到鼠标Y坐标位置
                        if has_mouse_y:
                            # 确保Y坐标在图表的有效范围内（0-100）
                            y_data = mouse_event.ydata
                            # 将Y坐标除以3，使得鼠标可以在更大范围内移动
                            y_data = y_data / 3
                                
                            # 四舍五入到整数值
                            new_y = int(round(y_data))
                            
                            # 再限制在应用程序要求的6-98范围内
                            new_y = max(6, min(98, new_y))
                            
                            self.current_array[x_coord] = new_y
                            status_text = f"选中点 #{x_coord} 并直接移动至Y={new_y}"
                        else:
                            status_text = f"选中点 #{x_coord}, 值: {self.current_array[x_coord]}"
                        
                        self.status_label.setText(status_text)
                        self.drag_status.setText(status_text)
                        self.drag_status.setStyleSheet("color: green; font-weight: bold;")
                        
                        # 更新选中点信息
                        self.update_point_info(x_coord, self.current_array[x_coord])
                        
                        # 重绘曲线，高亮显示选中的点
                        self.plot_array(self.current_array)
                        return True
        except Exception as e:
            self.status_label.setText(f"拾取事件错误: {str(e)}")
        
        return False

    def simulate_click(self):
        """模拟点击指定X坐标的点"""
        if len(self.current_array) == 0:
            QMessageBox.warning(self, "警告", "请先生成曲线再测试点击。")
            return
            
        x = self.x_pos_spin.value()
        if x >= len(self.current_array):
            QMessageBox.warning(self, "警告", f"X坐标 {x} 超出范围，最大值为 {len(self.current_array)-1}")
            return
            
        # 模拟选择指定点
        self.selected_point = x
        self.dragging = True
        
        # 保存当前值作为初始值
        self.initial_y = self.current_array[x]
        
        # 更新Y值输入框以匹配当前值
        self.y_value_spin.setValue(self.initial_y)
        
        status_text = f"选中点 #{x}, 值: {self.current_array[x]}"
        self.status_label.setText(status_text)
        self.drag_status.setText(status_text)
        self.drag_status.setStyleSheet("color: green; font-weight: bold;")
        
        # 更新选中点信息
        self.update_point_info(x, self.current_array[x])
        
        # 重绘曲线，高亮显示选中的点
        self.plot_array(self.current_array)

    def modify_point_value(self):
        """直接修改选中点的值"""
        if self.selected_point is None:
            QMessageBox.warning(self, "警告", "请先选中一个点再修改值")
            return
            
        # 获取新的Y值
        new_y = self.y_value_spin.value()
        idx = self.selected_point
        
        # 获取当前值作为初始值（避免initial_y可能不存在的问题）
        current_value = self.current_array[idx]
        
        # 更新数组
        self.current_array[idx] = new_y
        
        # 更新状态
        status_text = f"直接修改: 点 #{idx} 的值从 {current_value} 变为 {new_y}"
        self.status_label.setText(status_text)
        self.drag_status.setText(status_text)
        self.drag_status.setStyleSheet("color: blue; font-weight: bold;")
        
        # 更新选中点信息
        self.update_point_info(idx, new_y)
        
        # 重绘曲线
        self.plot_array(self.current_array)

    def reset_selection_state(self):
        """重置选择状态，避免重影"""
        self.dragging = False
        self.selected_point = None
        self.initial_y = None  # 重置初始值
        self.drag_status.setText("已重置选择状态")
        self.drag_status.setStyleSheet("color: black; font-weight: normal;")
        self.status_label.setText("生成了新的曲线")
        
        # 清除点信息显示
        self.point_info_area.setText("未选中任何点")
        self.pulse_info_label.setText("脉冲时间: --")
        
        # 重置X坐标选择器
        if hasattr(self, 'x_pos_spin'):
            self.x_pos_spin.setValue(0)
            
        # 重置Y值选择器
        if hasattr(self, 'y_value_spin'):
            self.y_value_spin.setValue(50)

    def on_key_press(self, event):
        """键盘事件处理"""
        if self.selected_point is None:
            return
            
        idx = self.selected_point
        current_value = self.current_array[idx]
        new_value = current_value
        
        # 方向键上下调整值
        if event.key == 'up':
            new_value = min(98, current_value + 1)
        elif event.key == 'down':
            new_value = max(6, current_value - 1)
        # 方向键左右切换选中点
        elif event.key == 'right' and idx < len(self.current_array) - 1:
            self.selected_point += 1
            idx = self.selected_point
            new_value = self.current_array[idx]
            self.initial_y = new_value
            if hasattr(self, 'x_pos_spin'):
                self.x_pos_spin.setValue(idx)
        elif event.key == 'left' and idx > 0:
            self.selected_point -= 1
            idx = self.selected_point
            new_value = self.current_array[idx]
            self.initial_y = new_value
            if hasattr(self, 'x_pos_spin'):
                self.x_pos_spin.setValue(idx)
                
        # 如果值有变化
        if new_value != current_value:
            self.current_array[idx] = new_value
            
        # 更新Y值输入框以匹配当前值
        if hasattr(self, 'y_value_spin'):
            self.y_value_spin.setValue(new_value)
            
        # 更新状态显示
        status_text = f"键盘调整: 点 #{idx}, 值: {new_value}"
        self.status_label.setText(status_text)
        self.drag_status.setText(status_text)
        
        # 更新选中点信息
        self.update_point_info(idx, new_value)
        
        # 更新图表
        self.update_plot_for_drag(idx, new_value)

    def adjust_value(self, delta):
        """增量调整选中点的值"""
        if self.selected_point is None:
            QMessageBox.warning(self, "警告", "请先选中一个点再调整值")
            return
            
        idx = self.selected_point
        current_value = self.current_array[idx]
        
        # 计算新值（处理小数增量）
        if abs(delta) < 1:
            # 对于小增量，四舍五入到整数
            new_value = int(round(current_value + delta))
        else:
            # 对于整数增量，直接加减
            new_value = current_value + int(delta)
            
        # 确保值在有效范围内
        new_value = max(6, min(98, new_value))
        
        # 如果值有变化
        if new_value != current_value:
            # 更新数组
            self.current_array[idx] = new_value
            
            # 更新Y值输入框
            if hasattr(self, 'y_value_spin'):
                self.y_value_spin.setValue(new_value)
                
            # 更新状态显示
            status_text = f"增量调整: 点 #{idx} 值从 {current_value} 变为 {new_value}"
            self.status_label.setText(status_text)
            self.drag_status.setText(status_text)
            
            # 更新选中点信息
            self.update_point_info(idx, new_value)
            
            # 更新图表
            self.update_plot_for_drag(idx, new_value)

    def update_point_info(self, idx, value):
        """更新选中点的详细信息显示"""
        if idx is None or idx < 0 or idx >= len(self.current_array):
            self.point_info_area.setText("未选中有效点")
            return
            
        # 计算角速度
        step_angle = 1.8  # 度
        pulse_time = value  # 脉冲时间(us)
        angular_velocity = step_angle / (pulse_time/1000)  # 度/秒
        
        # 单个脉冲时间
        single_pulse_time = 5  # 假设每个脉冲间隔是5us
        
        # 计算在此速度下旋转一圈所需时间
        full_circle_time = (360 / step_angle) * pulse_time / 1000  # ms
        
        # 构建详细信息文本
        info_text = f"<b>点 #{idx}</b> 信息:<br>"
        info_text += f"脉冲时间: <b style='color:blue'>{pulse_time} μs</b> | "
        info_text += f"角速度: <b style='color:red'>{angular_velocity:.2f} °/s</b> | "
        info_text += f"旋转一圈耗时: <b>{full_circle_time:.2f} ms</b>"
        
        # 更新信息显示区域
        self.point_info_area.setText(info_text)

    def update_control_visibility(self):
        """根据曲线类型更新控件的显示/隐藏逻辑"""
        curve_type = self.curve_type.currentText()
        
        # 只有自定义幂函数时显示幂参数控件
        if curve_type == "自定义幂函数":
            self.power_value.setEnabled(True)
        else:
            self.power_value.setEnabled(False)
            
        # 所有曲线类型都可以使用起始段和末尾段设置
        self.start_size.setEnabled(True)
        self.end_size.setEnabled(True)
        
        # 当曲线类型改变时，更新状态栏提示
        tips = {
            "线性": "线性曲线: 速度均匀变化，最基本的加减速曲线",
            "指数": "指数曲线: 速度指数级变化，初始加速和最终减速更快",
            "S型": "S型曲线: 三次曲线，起始和结束更平滑，适合大多数场景",
            "余弦": "余弦曲线: 基于余弦函数的平滑过渡，非常平滑的加减速",
            "抛物线": "抛物线: 二次曲线，加减速度逐渐变化，中间段减速明显",
            "自定义幂函数": f"幂函数: 自定义幂指数({self.power_value.value()})，可精确控制加减速特性"
        }
        
        self.status_label.setText(tips.get(curve_type, "选择曲线类型"))

    def update_plot_for_drag(self, idx, new_y):
        """更新曲线上拖动的点，而不重绘整个图形"""
        try:
            # 更新脉冲时长曲线的Y值
            y_data = self.line_plot.get_ydata()
            y_data[idx] = new_y
            self.line_plot.set_ydata(y_data)
            
            # 更新散点图数据
            if self.scatter_plot is not None:
                offsets = self.scatter_plot.get_offsets()
                offsets[idx, 1] = new_y
                self.scatter_plot.set_offsets(offsets)
            
            # 更新高亮点
            if self.highlight_point is not None:
                self.highlight_point.remove()
            self.highlight_point = self.ax.scatter([idx], [new_y], s=200, color='lime', 
                                  edgecolor='white', linewidth=2, alpha=1.0, zorder=3)
            
            # 更新角速度曲线
            step_angle = 1.8
            angular_velocity = [step_angle / (t/1000) for t in self.current_array]
            self.velocity_line.set_ydata(angular_velocity)
            
            # 更新数值标签
            for txt in self.ax.texts:
                txt.remove()
            self.ax.annotate(f'{new_y}', xy=(idx, new_y), xytext=(0, 10), textcoords='offset points',
                         ha='center', fontsize=9, fontweight='bold',
                         bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.7))
            
            # 只刷新画布，不重绘整个图形
            self.canvas.draw_idle()
        except Exception as e:
            self.status_label.setText(f"更新图表错误: {str(e)}")
            # 如果动态更新失败，则回退到完全重绘
            self.plot_array(self.current_array)
    
    def plot_array(self, arr):
        """绘制数组曲线"""
        # 完全清除图形
        self.ax.clear()
        self.figure.clf()  # 清除整个图形
        self.ax = self.figure.add_subplot(111)  # 重新创建子图
        
        if not arr or len(arr) == 0:
            self.canvas.draw()
            return
            
        # 获取x轴数据
        x_data = list(range(len(arr)))
        
        # 计算角速度
        step_angle = 1.8  # 度
        angular_velocity = [step_angle / (t/1000) for t in arr]  # 转换为度/秒
        
        # 设置坐标轴范围，横坐标自适应数组长度，确保坐标与值直接对应
        array_length = len(arr)
        x_margin = max(5, int(array_length * 0.05))  # 添加5%的边距，至少5个单位
        self.ax.set_xlim(-x_margin, array_length + x_margin)  # 横坐标自适应数组长度，留出余量
        self.ax.set_ylim(0, 105)  # 脉冲时长范围：0-105，留出余量
        
        # 设置刻度，确保值与位置一致
        self.ax.set_yticks(range(0, 105, 10))
        
        # 绘制脉冲时长曲线
        self.line_plot, = self.ax.plot(x_data, arr, '-', lw=1.5, color='blue', label='脉冲时长(us)', zorder=1)
        
        # 绘制可点击的散点图 - 使点更大更明显，大幅增加picker半径
        self.scatter_plot = self.ax.scatter(x_data, arr, s=100, color='darkblue', 
                                     alpha=0.7, edgecolor='yellow', linewidth=1.5, 
                                     picker=20, zorder=2)
        
        # 高亮选中的点
        self.highlight_point = None
        if self.selected_point is not None and 0 <= self.selected_point < len(arr):
            self.highlight_point = self.ax.scatter([self.selected_point], [arr[self.selected_point]], 
                       s=200, color='lime', edgecolor='white', linewidth=2,
                       alpha=1.0, zorder=3)
            
            # 添加文本标签，显示选中点的值
            self.ax.annotate(f'{arr[self.selected_point]}', 
                         xy=(self.selected_point, arr[self.selected_point]),
                         xytext=(0, 10), textcoords='offset points',
                         ha='center', fontsize=9, fontweight='bold',
                         bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.7))
        
        # 创建第二个y轴显示角速度
        ax2 = self.ax.twinx()
        self.velocity_line, = ax2.plot(x_data, angular_velocity, '-', lw=1, color='red', label='角速度(度/秒)', alpha=0.7)
        
        # 设置角速度轴的范围 - 从0开始
        ax2.set_ylim(0, 330)  # 角速度范围：0到330，让0点从X轴开始
        
        # 标记生效范围（如果已设置）
        if hasattr(self, 'range_start') and hasattr(self, 'range_end'):
            range_start_percent = self.range_start.value() / 100
            range_end_percent = self.range_end.value() / 100
            
            if range_start_percent > 0 or range_end_percent < 1:
                start_idx = int(len(arr) * range_start_percent)
                end_idx = int(len(arr) * range_end_percent)
                
                # 添加竖直线标记生效范围
                self.ax.axvline(x=start_idx, color='green', linestyle='--', alpha=0.7)
                self.ax.axvline(x=end_idx, color='green', linestyle='--', alpha=0.7)
                
                # 添加标注
                self.ax.text(start_idx, 105, "范围起点", color='green', fontsize=9,
                         ha='center', va='top', rotation=90, alpha=0.7)
                self.ax.text(end_idx, 105, "范围终点", color='green', fontsize=9,
                         ha='center', va='top', rotation=90, alpha=0.7)
                
                # 填充生效范围区域
                self.ax.axvspan(start_idx, end_idx, color='green', alpha=0.05)
        
        # 设置标题和标签
        curve_type = self.curve_type.currentText() if hasattr(self, 'curve_type') else "未知类型"
        self.ax.set_title(f"步进电机加减速曲线 - {curve_type}")
        self.ax.set_xlabel("步数")
        self.ax.set_ylabel("脉冲时长(us)")
        ax2.set_ylabel("角速度(度/秒)")
        
        # 添加图例
        lines1, labels1 = self.ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        self.ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        
        # 添加网格线使图表更清晰
        self.ax.grid(True, linestyle='--', alpha=0.7)
        
        # 确保图表响应鼠标事件
        self.figure.canvas.mpl_disconnect('button_press_event')
        self.figure.canvas.mpl_disconnect('button_release_event')
        self.figure.canvas.mpl_disconnect('motion_notify_event')
        self.figure.canvas.mpl_disconnect('pick_event')
        self.figure.canvas.mpl_disconnect('key_press_event')
        
        # 启用交互模式
        self.figure.canvas.setFocusPolicy(Qt.StrongFocus)
        self.figure.canvas.setFocus()
        
        # 强制完全重绘
        self.figure.tight_layout()  # 调整布局
        self.canvas.draw()
        self.canvas.flush_events()
        
        # 重新连接鼠标事件（因为figure.clf()会清除所有事件连接）
        self.cidpress = self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.cidrelease = self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.cidmotion = self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.cidpick = self.canvas.mpl_connect('pick_event', self.on_pick)
        self.cidkey = self.canvas.mpl_connect('key_press_event', self.on_key_press)
        
        # 计算总耗时
        total_time = sum(arr) * 5  # 假设每个脉冲间隔是5us
        
        # 更新总耗时显示，包含生效范围信息
        if hasattr(self, 'range_start') and hasattr(self, 'range_end'):
            range_start_percent = self.range_start.value() / 100
            range_end_percent = self.range_end.value() / 100
            
            if range_start_percent > 0 or range_end_percent < 1:
                start_idx = int(len(arr) * range_start_percent)
                end_idx = int(len(arr) * range_end_percent)
                effect_points = end_idx - start_idx
                
                # 添加生效范围信息
                range_info = f" | 生效范围: {start_idx}-{end_idx} (共{effect_points}点)"
                self.time_cost_label.setText(f"总耗时: {total_time/1000:.2f} ms{range_info}")
            else:
                self.time_cost_label.setText(f"总耗时: {total_time/1000:.2f} ms | 生效范围: 全部")
        else:
            self.time_cost_label.setText(f"总耗时: {total_time/1000:.2f} ms")

    def export_array(self):
        """导出为C数组格式"""
        if not self.current_array:
            QMessageBox.warning(self, "警告", "没有可导出的数组！")
            return
            
        array_name = "GeneratedCurve"
        s = f"int {array_name}[{len(self.current_array)}] = {{\n"
        for i, v in enumerate(self.current_array):
            s += f"{v},"
            if (i+1) % 10 == 0:
                s += "\n"
        s = s.rstrip(',\n') + "\n};"
        
        self.array_input.setText(s)
        QMessageBox.information(self, "成功", "数组已导出！")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = StepperCurveGenerator()
    window.show()
    sys.exit(app.exec_()) 