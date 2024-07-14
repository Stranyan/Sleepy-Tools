import colorsys, os, sys, subprocess, time, sqlite3, re, pysnooper, binascii, cProfile
from ping3 import ping
from datetime import datetime
from threading import Thread
from queue import Queue
from functools import partial
from scapy.all import *
from macpy import Mac
from mac_vendor_lookup import MacLookup
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
from ipaddress import ip_address

# from PyQt5 import QtWidgets, QtCore, QtGui
# from PyQt5.QtCore import QObject, pyqtSignal, Qt, QThread
# from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QMainWindow, QTableView
# from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QVBoxLayout, QTextEdit
# from PyQt5.QtWidgets import QLineEdit, QShortcut, QHeaderView, QAbstractItemView, QGridLayout
# from PyQt5.QtGui import QStandardItem, QStandardItemModel, QKeySequence, QColor

from rich import print

DEBUG_MODE = True
PING_ONCE = True
# 获取当前时间戳，并转换为字符串
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
TABLENAME = f"ping_results_{timestamp}"

# app = QtWidgets.QApplication(sys.argv) # 创建一个QApplication对象
# layout: QVBoxLayout
# ping_result_list: List[Optional[str]] = []

# 输入值，输出IP列表
class IPGenerator:
    def __init__(self):
        pass
    
    def from_string(self, ip_string):
        try:
            ip_getted = self.get_ip(ip_string)
            try:
                address = ip_address(ip_getted)#检测输入是不是IP
                if DEBUG_MODE:
                    print("IP地址：", address)
                    print("IP Version:", address.version)
                    print("是否是专用地址:", address.is_private)
                    print("是否是公网地址:", address.is_global)
                    print("是否是多播地址:", address.is_multicast)
                    print("是否是环回地址:", address.is_loopback)
                    print("是否是link-local保留:", address.is_link_local)
                    print("判断地址是否未指定:", address.is_unspecified)
                    print("IP地址16进制:", binascii.hexlify(address.packed))
                return ip_string
            except:
                return []
        except:#如果不是，就手动检测
            # print(ip_string)
            if type(ip_string) == list:
                return self.generate_ips(ip_string)
            else:
                ip_pattern = re.compile(r'^\d{1,3}(-\d{1,3})?\.\d{1,3}(-\d{1,3})?\.\d{1,3}(-\d{1,3})?\.\d{1,3}(-\d{1,3})?$')
                if ip_pattern.match(ip_string):#首先检测有没有IP标志性的三个‘.’
                    print(f'{ip_string}有三个点') if DEBUG_MODE else None
                    if '-' in ip_string:#因为功能需要，输入可能会是‘192.168.0.1-255’形式的
                        print(f'{ip_string}有‘-’') if DEBUG_MODE else None
                        var = ip_string.split(".")#如果确认是，就把它输出
                        print(f'一开始输出的是{var}') if DEBUG_MODE else None
                        return self.generate_ips(var)
                    else:
                        return self.generate_ips(ip_string)
                else:
                    return self.generate_ips(ip_string)
    
    def get_ip(self, domain):
        address = socket.getaddrinfo(domain, 'http')#防止输入的是域名，在这儿给解析成IP
        return address[0][4][0]

    def generate_ips(self, var=[]):
        print(f'DEBUG：生成输入的是{var}') if DEBUG_MODE else None
        ips = []
        if var != []:
            if len(var) == 4:
                self.var1 = var[0]
                self.var2 = var[1]
                self.var3 = var[2]
                self.var4 = var[3]
                for v1 in self._expand_var(self.var1):
                    for v2 in self._expand_var(self.var2):
                        for v3 in self._expand_var(self.var3):
                            for v4 in self._expand_var(self.var4):
                                ip = f"{v1}.{v2}.{v3}.{v4}"
                                ips.append(ip)
                print(f'DEBUG：生成的IP是{ips}') if DEBUG_MODE else None
            elif len(var) == 1:
                ips = var[0]
                print(f'DEBUG：长度是1，生成的IP是{ips}') if DEBUG_MODE else None
            else:
                ips = var[0] if isinstance(var, list) else var
                print(f'DEBUG：没生成，输出第0个是{ips}') if DEBUG_MODE else None
            return ips
        else:
            print(f'DEBUG：没生成，直接输出{ips}') if DEBUG_MODE else None
            return var
    
    def _expand_var(self, var):
        if var != '':
            if "-" in var:
                start, end = var.split("-")
                return range(int(start), int(end) + 1)
            else:
                try:
                    return [int(var)]
                except:
                    return ''
        else:
            return var

    def useful_ip_1(self):
        ips = [f"192.168.0.{i}" for i in range(0, 255)]
        return ips

    def useful_ip_2(self):
        ips = [f"192.168.1.{i}" for i in range(0, 255)]
        return ips

    def useful_ip_3(self):
        ips = [f"192.168.20.{i}" for i in range(0, 255)]
        return ips

    def useful_ip_internet(self):
        ips = ["baidu.com", "google.com", "bing.com", "163.com", "github.com"]
        return ips

    def useful_ip_test(self):
        ips = ["baidu.com", "google.com", "bing.com", "163.com", "github.com", "192.168.0.1", "192.168.0.50", "192.168.0.10", "1-9.com"]
        return ips

# 执行 ping 和 arp 多线程
class PingARPExecutor:
    def __init__(self):
        self.completed_tasks = 0
        pass

    def ping(self, ip):
        # 执行 Ping 操作
        result = ping(ip, timeout=2, unit='ms', size=56)
        return result

    # 添加 arp 方法
    def arp(self, ip):
        try:
            arp_request = Ether(dst='ff:ff:ff:ff:ff:ff') / ARP(pdst=ip)
            arp_response = srp(arp_request, timeout=2, verbose=0)[0]
            
            if arp_response:
                target_mac = arp_response[0][1].hwsrc
                return target_mac
            else:
                return None
        except Exception as e:
            return e

    def ping_and_arp(self, ip, count):
        start_time = time.time()
        # 这里执行 Ping 和 ARP 操作，返回结果
        ping_result = self.ping(ip)
        arp_result = self.arp(ip)
        self.completed_tasks += 1  # 每完成一个任务，增加计数器的值
        self.compute_execute_time(count, self.completed_tasks, start_time)
        # print('')
        # 返回结果
        return ping_result, arp_result

    def execute(self, ips):
        # print(len(ips))
        # 使用 ThreadPoolExecutor 处理 IP 列表中的每个 IP
        with ThreadPoolExecutor(max_workers=len(ips)+10) as executor:
        # with self.executor as executor:
            # 提交每个 IP 的任务
            results = {executor.submit(self.ping_and_arp, ip, len(ips)): ip for ip in ips}
            # 获取结果
            all_results = {}
            for future in results:
                ip = results[future]
                try:
                    ping_result, arp_result = future.result()
                    all_results[ip] = {'ping': ping_result, 'arp': arp_result}
                except Exception as e:
                    all_results[ip] = {'ping': e, 'arp': e}

        return all_results
    
    def compute_execute_time(self, count=0, completed_tasks=0, start_time=0):
        progress_percentage = (completed_tasks / count) * 100
        # 获取当前时间戳
        timestamp = time.time()
        # 将时间戳转换为本地时间的结构化时间
        local_time = time.localtime(timestamp)
        # 从结构化时间中提取时、分、秒信息
        hour = local_time.tm_hour
        minute = local_time.tm_min
        second = local_time.tm_sec
        microsecond = int((timestamp - int(timestamp)) * 1000)

        now = time.time()
        running_time = now - start_time
        # print('\r' + f'{progress_percentage},执行耗时:{running_time}', end='', flush=True)
        # print(f'{progress_percentage},执行耗时:{running_time}')

class ResultAnalyzer:
    def __init__(self):
        pass

    def analyze_ping(self, ping_result):
        analyzed_ping = []
        
        delay = 2000.00
        status = False
        ttl = 0
        
        if ping_result:
            if isinstance(ping_result[0], (float, int)) and len(ping_result) > 1:
                delay = round(ping_result[0], 2)
                ttl = ping_result[1]
                status = True
            elif isinstance(ping_result[0], str) and 'ms' in ping_result[0] and len(ping_result) > 1:
                delay_str = ping_result[0].replace('ms', '').strip()
                try:
                    delay = round(float(delay_str), 2)
                    ttl = ping_result[1]
                    status = True
                except ValueError:
                    pass

        analyzed_ping.append((status, delay, ttl))
        
        return analyzed_ping

    def validate_mac_address(self, mac_address):
        # 使用正则表达式验证 MAC 地址格式是否正确
        mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
        if mac_pattern.match(mac_address):
            # 对 MAC 地址进行验证和格式化
            try:
                target_corp = MacLookup().lookup(mac_address)
                return target_corp
            except Exception as e:
                # print(e)
                return False
        else:
            return False

    def analyze_arp(self, arp_result):
        analyzed_arp = []
        target_corp = self.validate_mac_address(arp_result) if arp_result else None
        analyzed_arp.append((arp_result, target_corp))
        return analyzed_arp

    def analyze_results(self, results):
        analyzed_results = {}

        for ip, result in results.items():
            ping_result = result.get('ping')
            arp_result = result.get('arp')

            ping_analyzed = self.analyze_ping(ping_result)
            arp_analyzed = self.analyze_arp(arp_result)

            analyzed_results[ip] = {
                'Status': ping_analyzed[0][0],
                'Delay': ping_analyzed[0][1],
                'TTL': ping_analyzed[0][2],
                'MAC': arp_analyzed[0][0],
                'Hardware': arp_analyzed[0][1]
            }

        return analyzed_results

    def sort_data(self, item):     
        # 使用 sorted() 函数对字典的值进行排序，根据延迟来排序
        sorted_results = sorted(item.items(), key=lambda x: x[1]['Delay'], reverse=False)
        # 添加Rank值
        rank = 1
        for ip, result in sorted_results:
            result['Rank'] = rank
            rank += 1
            result['Delay'] = str(result['Delay']) + 'ms'

        return sorted_results

    def dic_results(self,sorted_results):
        analyzed_results = []
        # 构建分析结果字典
        for ip, result in sorted_results:
            analyzed_result = {
                'IP': ip,
                'Status': result['Status'],
                'Delay': result['Delay'],
                'TTL': result['TTL'],
                'MAC': result['MAC'],
                'Hardware': result['Hardware'],
                'Rank': result['Rank']
            }
            analyzed_results.append(analyzed_result)

        return analyzed_results

# class StandardItem(QtGui.QStandardItem):
#     def __lt__(self, other):
#         try:
#             # 根据列索引选择不同的排序规则
#             column_index = self.column()
#             if column_index == 0:  # 第一列按IP排序
#                 return ip_address(self.text()) < ip_address(other.text())
#             # elif column_index == 1:  # 第二列按字符串排序
#             #     return self.text() < other.text()
#             elif column_index == 2:  # 第三列按数字排序（先剔除ms再转换为整数）
#                 self_value = float(self.text().rstrip('ms'))
#                 other_value = float(other.text().rstrip('ms'))
#                 return self_value < other_value
#             elif column_index in [3, 6]:  # 第四列和第七列按数字排序
#                 self_value = int(self.text())
#                 other_value = int(other.text())
#                 return self_value < other_value
#             # elif column_index in [4, 5]:  # 第五列和第六列按字符串排序，但是需要先剔除False和None进行排序，然后再把False和None添加在后续
#             #     if self.text() in ['False', 'None']:
#             #         return -1
#             #     elif other.text() in ['False', 'None']:
#             #         return 1
#             #     else:
#             #         return self.text() < other.text()
#             else:
#                 # 其他列按默认的文本排序
#                 return super().__lt__(other)
#         except:
#             return super().__lt__(other)

# class DisplayGUI(QWidget):
class DisplayGUI():
    # def initUI_table(self):
    #     table = self.table
    #     model = self.model
    #     # # 创建主布局
    #     # main_layout = QHBoxLayout(self)
    #     # # 创建表格布局
    #     # table_layout = QVBoxLayout()
    #     # 设置表格行数和列数
    #     model.setRowCount(10)
    #     model.setColumnCount(7)
    #     # 设置表头
    #     model.setHorizontalHeaderLabels(['IP', 'Status', 'Delay', 'TTL', 'MAC', 'Hardware', 'Rank'])
    #     # 将数据模型设置给表格视图
    #     table.setModel(model)
    #     # 设置列宽度自适应模式
    #     header = table.horizontalHeader()
    #     header.setSectionResizeMode(QHeaderView.ResizeToContents)
    #     header.setSectionResizeMode(5, QHeaderView.Stretch)  # Hardware 列填满剩余空间
    #     table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    #     self.layout.addWidget(table)

    #     # 设置窗口布局
    #     self.setLayout(self.layout)
    #     self.show()

    # def create_ping_button(self, text, click_function, layout=None):
    #     button = QPushButton(text)
    #     button.clicked.connect(click_function)
    #     if layout:
    #         layout.addWidget(button)
    #     return button

    # def get_generate_ip(self, var='', var1='', var2='', var3='', var4=''):
    #     # 创建 IPGenerator 对象
    #     if var == '':
    #         var_data = [var1, var2, var3, var4]
    #     else:
    #         var_data = var
    #     ip_g = IPGenerator()
    #     generated_ip = ip_g.from_string(var_data)
    #     # print(generated_ip)
    #     return generated_ip

    # def rgb_to_hex(self, r, g, b):
    #     return ('{:02X}' * 3).format(r, g, b)

    # def hsv_to_rgb(self, h, s, v):
    #     r, g, b = colorsys.hsv_to_rgb(h, s, v)
    #     return (int(r*255), int(g*255), int(b*255))

    def map_range(self, value, min_value, max_value, new_min, new_max):
        return (value - min_value) * (new_max - new_min) / (max_value - min_value) + new_min

    # def change_color(self, status, rank, count):
    #     if status:
    #         h = self.map_range(75,0,255,0,1)
    #     else:
    #         h = self.map_range(0,0,255,0,1)

    #     h,s,v = h,self.map_range(200,0,255,0,1),self.map_range(int(rank),0,int(count),0.9,0.1)
    #     bg_rgb = self.hsv_to_rgb(h,s,v)
    #     r,g,b = bg_rgb[0],bg_rgb[1],bg_rgb[2]

    #     # print('v', v)
    #     fg = 1 - v
    #     # print(fg)
    #     if 0.3 < fg <= 1:
    #         fg = round(self.map_range(fg,0,1,200,255))
    #         # fg = round(self.map_range(0.9,0,1,0,255))
    #     elif 0 <= fg <= 0.3:
    #         fg = round(self.map_range(fg,0,1,0,55))
    #         # fg = round(self.map_range(0.1,0,1,0,255))
        
    #     # print('fg', fg)

    #     bg_color = QColor(r,g,b)
    #     fg_color = QColor(fg,fg,fg)
    #     return bg_color, fg_color

    # def set_table_item(self, row, column, item, status, rank, count):
    #     """
    #     设置表格项的值、颜色、对齐方式等。
        
    #     Args:
    #         row (int): 行索引
    #         column (int): 列索引
    #         item (Any): 要设置的值
    #         status (str): 状态值，用于确定颜色
    #         rank (int): 排名值，用于确定颜色
    #         count (int): 计数值，用于确定颜色
        
    #     Returns:
    #         None
        
    #     """
    #     table = self.table
    #     model = self.model
    #     item_data = QStandardItem(str(item))
    #     item_data = StandardItem(str(item))
    #     bg_color, fg_color = self.change_color(status, rank, count)
    #     item_data.setBackground(bg_color)
    #     item_data.setForeground(fg_color)
    #     item_data.setTextAlignment(Qt.AlignCenter)  # 居中对齐
    #     model.setItem(row, column, item_data)
    #     table.update()
    #     return

    def delete_database(self):
        # 连接到 SQLite 数据库（如果数据库不存在，则会自动创建）
        conn = sqlite3.connect('powerping.db')
        print('数据库连接成功')
        # 创建一个游标对象，用于执行 SQL 语句
        cursor = conn.cursor()
        # 在写入数据之前清空表格
        cursor.execute(f"DELETE FROM {TABLENAME}")
        print('清空表格成功')

    def display_data_in_treeview(self, analyzed_results=None):
        # print('显示为', analyzed_results)
        # 连接到 SQLite 数据库（如果数据库不存在，则会自动创建）
        conn = sqlite3.connect('powerping.db')
        print('数据库连接成功')
        # 创建一个游标对象，用于执行 SQL 语句
        cursor = conn.cursor()

        # 创建一个名为 ping_results_{timestamp} 的表格，包含 IP、Status、Delay、TTL、MAC、Hardware 和 Timestamp 七列
        cursor.execute(f'''CREATE TABLE IF NOT EXISTS {TABLENAME}
                        (IP TEXT, Status TEXT, Delay TEXT, TTL TEXT, MAC TEXT, Hardware TEXT, Timestamp DATETIME)''')

        # # 创建一个名为 ping_results 的表格，包含 IP、Status、Delay、TTL、MAC、Hardware 和 Timestamp 七列
        # cursor.execute('''CREATE TABLE IF NOT EXISTS ping_results_{timestamp}
        #                 (IP TEXT, Status TEXT, Delay TEXT, TTL TEXT, MAC TEXT, Hardware TEXT, Timestamp DATETIME)''')
        print('表格创建成功')

        # 模拟记录多个设备的数据
        devices_data = [
            {'IP': '192.168.0.1', 'Status': 'True', 'Delay': 10.5,  'TTL': 10, 'MAC': '00:25:96:C8:D7:4F', 'Hardware': 'Intel'},
            {'IP': '192.168.0.2', 'Status': 'True', 'Delay': 20.3,  'TTL': 10, 'MAC': '00:25:96:C8:D7:4F', 'Hardware': 'Intel'},
            {'IP': '192.168.0.1', 'Status': 'False', 'Delay': 15.2, 'TTL': 10, 'MAC': '00:25:96:C8:D7:4F', 'Hardware': 'Intel'},
            {'IP': '192.168.0.3', 'Status': 'False', 'Delay': 22.8, 'TTL': 10, 'MAC': '00:25:96:C8:D7:4F', 'Hardware': 'Intel'},
        ]

        if PING_ONCE:
            print('PING_ONCE')

        # 提交更改
        conn.commit()

        # 插入数据
        for data in analyzed_results:
            print(data)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(f"INSERT INTO {TABLENAME} (IP, Status, Delay, TTL, MAC, Hardware, Timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)", (data['IP'], data['Status'], data['Delay'], data['TTL'], data['MAC'], data['Hardware'], timestamp))

        # 提交更改并关闭连接
        conn.commit()
        conn.close()

        return
    
    def show_data(self):
        # 重新连接到数据库
        conn = sqlite3.connect('powerping.db')
        cursor = conn.cursor()

        # 从表格中读取数据
        cursor.execute("SELECT * FROM ping_results")
        rows = cursor.fetchall()

        # 打印结果
        for row in rows:
            print(row)

        # 关闭连接
        conn.close()

        return

    def execute_program(self, input_ip):
        start_time = time.time()
        ip_g = IPGenerator()
        ip_g = ip_g.from_string(input_ip)
        # print(type(ip_g))
        # 获取生成的 IP 地址列表
        if isinstance(ip_g, list):
            ips = ip_g
        elif isinstance(ip_g, str):
            print('INPUT TYPE ERROR')
            return TypeError
        else:
            ips = ip_g.generate_ips()
        executor = PingARPExecutor()
        data = executor.execute(ips)
        print('data', data)

        ra = ResultAnalyzer()
        results = ra.analyze_results(data)
        delay = ra.sort_data(results)
        dic = ra.dic_results(delay)
        self.display_data_in_treeview(dic)
        # self.display_data_in_treeview()
        # print(dic)

        now = time.time()
        running_time = now - start_time
        print('')
        print(f'主进程耗时:{running_time}')
        return
    

input_ip = input('请输入要扫描的 IP 地址：')
dg = DisplayGUI()
for i in range(10):
    dg.execute_program(input_ip)