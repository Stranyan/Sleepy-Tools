import json, os, sqlite3
from datetime import datetime, timedelta

from flask import Flask, render_template, request, jsonify, redirect, Response
from flask_sqlalchemy import SQLAlchemy

import float32to10
from collections import OrderedDict

app = Flask(__name__)

# 定义路由，手动为每个 HTML 文件创建路由
# 路由：读取数据库中的数据，并传递给模板
@app.route('/function/get_db_table_data', methods=['GET', 'POST'])
def get_db_table_data():
    # 重新连接到数据库
    conn = sqlite3.connect('powerping.db')
    cursor = conn.cursor()

    # 从表格中读取数据，并按照 Timestamp 字段进行降序排序
    cursor.execute("SELECT * FROM ping_results ORDER BY Timestamp DESC")
    rows = cursor.fetchall()

    # 关闭连接
    conn.close()
    time_list = [{'Timestamp': row[6]} for row in rows]
    unique_times = list(set(row['Timestamp'] for row in time_list))
    current_time = datetime.now()
    # 计算unique_times列表中每个时间和当前时间的间隔大小
    time_gaps = [(time, abs(current_time - datetime.strptime(time, "%Y-%m-%d %H:%M:%S"))) for time in unique_times]
    # 找到时间间隔最小的时间
    min_time, min_gap = min(time_gaps, key=lambda x: x[1])
    # 筛选出时间间隔为最小间隔的行数据
    filtered_data = [row for row in rows if row[6] == min_time]
    # 将数据转换为 JSON 格式
    json_data = [{'IP': row[0], 'Status': row[1], 'Delay': row[2], 'TTL': row[3], 'MAC': row[4], 'Hardware': row[5], 'Timestamp': row[6]} for row in filtered_data]
    # 返回 JSON 格式数据给前端
    return jsonify(json_data)

@app.route('/function/get_db_status_counts',methods=['GET','POST'])#路由
def get_db_status_counts():
    # 从数据库中读取数据
    # 重新连接到数据库
    conn = sqlite3.connect('powerping.db')
    cursor = conn.cursor()

    # 从表格中读取数据
    cursor.execute("SELECT * FROM ping_results")
    rows = cursor.fetchall()
    # 关闭连接
    conn.close()

    # 计算出True和False的数量
    true_count = sum(1 for row in rows if row[1] == '1')  # 假设Status列在第二个位置
    print('true_count', true_count)
    false_count = sum(1 for row in rows if row[1] == '0')
    print('false_count', false_count)
    return jsonify({'true_count': true_count, 'false_count': false_count})

@app.route('/function/convert_hex')
def get_data():
    hex_str = request.args.get('hex_str')
    if hex_str is None:
        return jsonify({})  # 返回一个空的 JSON 对象
    else:
        data = OrderedDict()
        data = float32to10.main_app(hex_str)
        print(data)
        print(json.dumps(data, indent=4, ensure_ascii=False)) 
        # return jsonify(**data)
        return Response(json.dumps(data), mimetype='application/json')

@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html')

@app.route('/chart.html')
def chart():
    return render_template('chart.html')

@app.route('/tools.html')
def tools():
    return render_template('tools.html')

@app.route('/empty.html')
def empty():
    return render_template('empty.html')

@app.route('/form.html')
def form():
    return render_template('form.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/tab-panel.html')
def tab_panel():
    return render_template('tab-panel.html')

@app.route('/table.html')
def table():
    return render_template('table.html')

@app.route('/ui-elements.html')
def ui_elements():
    return render_template('ui-elements.html')

# 定义错误处理程序，用于处理所有未定义路由的情况
@app.errorhandler(404)
def page_not_found(error):
    # 重定向到指定的路由，这里假设重定向到 index 函数处理的路径
    return redirect('/')

# @app.route('/register', methods=['POST'])
# def register():
#     # 从表单获取数据
#     original_data = request.get_data()
#     data = request.get_json()  # 获取POST请求的JSON数据
#     print(f"json 方式接收的数据为: {data}")
#     print(f"原始方式获取的数据为: {original_data}")
#     print(f"json解析后: {json.loads(original_data)}")
#     username = data.get('username')
#     password = data.get('password')
#     email = data.get('email')

#     # todo 添加代码将数据保存到数据库
#     # 返回一个成功消息
#     return jsonify({"status": "success", "message": f"Registration successful for username: {username}, email: {email}"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
