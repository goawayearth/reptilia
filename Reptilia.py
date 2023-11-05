import csv
import datetime
import hashlib
import logging
import os
import re
import threading
import time
import urllib.request
from bs4 import BeautifulSoup
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from db.db_access import insert_hisq_data, findall_data
import tkinter as tk
from tkinter import *
import mplfinance as mpf
import pandas as pd
import codecs
import tkinter as tk
from PIL import Image, ImageSequence, ImageTk

choice='600519'
flag=1
gelidianqi='000651'
isrunning = True

# 爬虫工作时间间隔
interval = 5


# start logging 基础设置
logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(threadName)s - '
                                              '%(name)s - %(funcName)s - %(levelname)s - %(message)s')
'''%(asctime)s表示日志记录时间，%(threadName)s表示线程名称，%(name)s表示记录器名称，%(funcName)s表示调用日志记录器的函数名，
%(levelname)s表示日志级别，%(message)s表示日志消息本身。'''
logger = logging.getLogger(__name__)

# 网址
url = 'https://q.stock.sohu.com/cn/'+choice+'/lshq.shtml'


def validateUpdate(html):
    """验证数据是否更新，更新返回True，未更新返回False"""
    global choice
    # 创建md5对象
    '''第一行创建了一个名为md5obj的MD5对象，可以用来计算MD5哈希值。
       第二行调用了md5obj的update方法，将要计算哈希值的字符串(html)进行了编码(encoding='GBK')并更新到md5obj中。
       第三行调用了md5obj的hexdigest方法，计算出最终的哈希值，并将其赋值给了变量md5code。'''
    md5obj = hashlib.md5()
    md5obj.update(html.encode(encoding='GBK'))
    md5code = md5obj.hexdigest()

    old_md5code = ''
    f_name = choice+'.txt'
    # 如果文件存在读取文件内容
    if os.path.exists(f_name):
        with open(f_name, 'r', encoding='GBK') as f:
            old_md5code = f.read()

    if md5code == old_md5code:
        print('数据没有更新')
        return False
    else:
        # 更新的话将数据重新写入文件
        with open(f_name, 'w', encoding='GBK') as f:
            f.write(md5code)
        print('数据更新')
        return True


def controlthread_body():
    '''用来改变爬虫的时间间隔或者结束爬虫'''
    global interval, isrunning
    while isrunning:
        # 控制爬虫工作计划
        i = input('输入Bye终止爬虫，输入数字改变爬虫工作间隔，单位秒：')
        logger.info('控制输入{0}'.format(i))
        try:
            interval = int(i)
        except ValueError:
            if i.lower() == 'bye':
                isrunning = False


def workthread_body():
    global interval, isrunning, url, choice, flag

    while isrunning:
        if istradtime():
            logger.info('交易时间，爬虫休眠1小时...')
            time.sleep(60 * 60)
            continue
        logger.info('爬虫开始工作...')

        chrome_options=Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(chrome_options=chrome_options,executable_path=r'chromedriver_win32/chromedriver')

        driver.get(url)
        content = driver.page_source.encode('utf-8')
        driver.quit()

        sp = BeautifulSoup(content, 'html.parser')
        # 返回div标签中的html字符串
        div = sp.select('table#BIZ_hq_historySearch')
        # 返回html列表中第一个元素
        divstring = div[0]

        if validateUpdate(divstring):
            trlist = sp.select('table#BIZ_hq_historySearch tbody tr')
            data = []
            for tr in trlist[1:]:  # 不要第一行
                if tr == '':
                    continue
                rows = re.search(
                    r'<td class="e1">(\w+-\w+-\w+)</td><td>(\w*.\w*)</td><td>(\w*.\w*)</td><td>(.\w*.\w*)</td><td>(.\w*.\w*%)</td><td>(\w+.\w+)</td><td>(\w+.\w+)</td><td>(\w+)</td><td>(\w+.\w+)</td><td>(\w*.\w*%)</td>',
                    str(tr))
                fields = {}
                fields['Date'] = rows.group(1)
                fields['Open'] = float(rows.group(2))
                fields['Close'] = float(rows.group(3))
                fields['Low'] = float(rows.group(6))
                fields['High'] = float(rows.group(7))
                fields['Volume'] = int(rows.group(8))
                data.append(fields)

            for row in data:
                if choice=='835640':
                    row['Symbol'] = 'FUSHIDA'
                if choice=='600519':
                    row['Symbol'] = 'AAPL'
                if choice=='000651':
                    row['Symbol']='GELIDIANQI'
                print(row)
                insert_hisq_data(row)
        '''只有在一次爬虫操作结束之后才能修改choice的值，不能该之前读的数据，判断的时候和插入的时候是别的choice'''
        if flag==1:
            choice='600519'
        if flag==2:
            choice='835640'
        if flag==3:
            choice='000651'
        logger.info('爬虫休眠{0}秒...'.format(interval))
        time.sleep(interval)


#"判断交易时间"
def istradtime():
    now = datetime.datetime.now()
    df = '%H%M%S'
    strnow = now.strftime(df)
    starttime = datetime.time(12, 30).strftime(df)
    endtime = datetime.time(12, 35).strftime(df)
    '''now.weekday()返回当前日期的星期几，从0（周一）到6（周日）'''
    if now.weekday() == 5 or now.weekday() == 6 or (strnow < starttime or strnow > endtime):
        return False
    # 工作时间
    return True


# "添加动态图"
class AnimatedGIF(tk.Label):
    def __init__(self, master, path):
        self.gif_path = path
        self.gif = self.load_gif()  # "self.gif是指一个列表，其中包含动画中所有帧的Image对象。"
        tk.Label.__init__(self, master, image=self.gif[0], bg='white')
        self.current_frame = 0   # current_frame 实例变量来跟踪当前帧
        self.next_frame()  # 最后调用self.next_frame()方法开始播放GIF

    # 保存动画帧并播放
    def load_gif(self):  # load_gif 方法打开指定路径的 GIF 文件
        gif = Image.open(self.gif_path)    # Image.open 函数加载 GIF 文件
        frames = []
        try:
            while True:
                frames.append(ImageTk.PhotoImage(gif.copy()))  # 调用 ImageTk.PhotoImage 函数来创建每一帧的 ImageTk.PhotoImage 对象
                gif.seek(len(frames))  #  使用 gif.seek(len(frames)) 将文件指针移到下一个帧
        except EOFError:  # end of sequence
            pass
        return frames

    # 实现自动循环播放
    def next_frame(self):
        self.current_frame += 1  # current_frame 加一，以便下一次显示下一帧
        if self.current_frame >= len(self.gif):
            self.current_frame = 0
        self.config(image=self.gif[self.current_frame])
        self.after(50, self.next_frame)  # 归调用 next_frame 方法


# "创建母窗口"
def creatWindow():
    global choice,flag
    get_data()

    "创建主界面"
    window = tk.Tk()
    window.title('股票价格分析')
    window.geometry('800x700')
    window.withdraw()  # 先将窗口隐藏

    "登录界面"
    '''首先，通过LoginWindow(window)创建一个LoginWindow对象，并将其赋值给变量login_window。
    然后，使用grab_set()方法将该登录窗口设置为模态窗口，这意味着该窗口会阻止用户操作其他窗口，直到该窗口关闭为止。模态窗口常用于需要用户先进行登录或其他操作才能继续执行的场景中。
    最后，使用protocol()方法为该登录窗口设置了一个关闭窗口的回调函数。在这里，当用户关闭该登录窗口时，会自动触发回调函数window.quit，该函数会退出应用程序并关闭所有窗口。'''
    login_window = LoginWindow(window)
    login_window.grab_set()  # 模态窗口，先浮动出此窗口，用于登录界面
    login_window.protocol("WM_DELETE_WINDOW", window.quit)  # 指定当窗口被关闭时的处理方式。

    "依据选择更新自己的数据"
    def on_option_changed(*args):  # 依据选择更新自己的数据
        global flag
        selected_value = selected_option.get()
        if selected_value=='富士达':
            flag=2
        if selected_value=='茅台' :
            flag=1
        if selected_value=='格力电器':
            flag=3
        get_data();
        ConfigTable(table, canvas, scrollbar)

    options = ["茅台", "富士达", "格力电器"]

    "添加动态图"
    # 创建一个AnimatedGif实例，并将其添加到窗口上
    gif_label = AnimatedGIF(window, 'welcome.gif')


    gif_label.pack()

    #""添加头部图片"
    #html_gif = tk.PhotoImage(file="welcome.gif")
    #label = Label(window, image=html_gif)
    #label.pack()


    "下拉框"
    # 创建一个下拉框selected_option   StringVar
    selected_option = tk.StringVar(window)
    # 下拉框默认值设为‘贵州茅台’
    selected_option.set(options[0])
    # 创建下拉框的下拉菜单
    option_menu = tk.OptionMenu(window, selected_option, *options,command=on_option_changed)
    option_menu.place(x=180,y=150)
    # 不能用网格，因为python不允许同时使用pack和grid option_menu.grid(row=1, column=0, padx=10, pady=10)

    "添加两个按钮写在后面，因为用到了刷新函数"

    "设置滚动条 and 表格"
    # 带有滚动条的Canvas是一种用户界面控件，它可以在用户界面上显示大量的内容，同时支持滚动条进行浏览
    canvas = tk.Canvas(window, width=1000, height=450)

    # 创建一个Scrollbar对象，指定方向为竖直方向，并将其绑定到window窗口上
    # 并将canvas的垂直滚动条与scrollbar对象绑定
    scrollbar = tk.Scrollbar(window, orient="vertical", command=canvas.yview)

    # 创建一个Frame对象，并将其绑定到canvas上,用于放置表格
    scrollable_frame = tk.Frame(canvas)

    # 创建一个回调函数，用于更新canvas的滚动区域
    # 将scrollable_frame的大小作为滚动区域的大小
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    # 在canvas上创建一个窗口，用于放置scrollable_frame
    # 并将scrollable_frame放置在该窗口的左上角
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    # 将canvas的垂直滚动条设置为scrollbar对象
    canvas.configure(yscrollcommand=scrollbar.set)

    # 在scrollable_frame上添加一个Frame组件，用于放置表格
    table = tk.Frame(scrollable_frame)

    ConfigTable(table, canvas, scrollbar)

    def refresh():
        ConfigTable(table,canvas,scrollbar)

    "添加两个按钮"
    tk.Button(window, text='K线图', width=6, height=1, bg='yellow', command=create_subwindow).place(x=330, y=150,
                                                                                                    anchor='nw')
    tk.Button(window, text='刷新', width=6, height=1, bg='light green', command=refresh).place(x=430, y=150,
                                                                                               anchor='nw')

    window.mainloop()


# "创建子窗口——K线图  子窗口调用下面的class函数"
def create_subwindow():
    t = tk.Toplevel()
    t.geometry('800x600')
    t.wm_title("K线图")
    sub_window = SubWindiw()
    sub_window.subWindow(t)

class SubWindiw:
    def __init__(self):
        pass

    def subWindow(self, root_frame):

        df=get_data()
        # 创建主框架
        main_frame = tk.Frame(root_frame)
        main_frame.pack()

        # 创建股票图形输出框架
        self.stock_graphics = tk.Frame(root_frame, relief='raised')
        self.stock_graphics.pack(expand=1, fill='both', anchor='center')

        # data = data.sort_index(ascending=True)  # 将时间顺序升序，符合时间序列
        # data = data[data.index < end_date][data.index > start_date]

        my_color = mpf.make_marketcolors(
            up='tab:red',  # 设置上涨时的颜色
            down='tab:green',  # 设置下跌时的颜色
            wick='black',  # 设置K线上下影线的颜色
            edge='black',  # 设置K线边缘线的颜色
            volume='gray',  # 设置成交量柱形图颜色
            inherit=True  # 继承父级颜色设置
        )
        # 设置图表的背景色

        my_style = mpf.make_mpf_style(
            base_mpf_style='yahoo',  # 继承Yahoo风格
            y_on_right=False,  # 设置y轴刻度线在左侧
            gridstyle=':',  # 设置网格线风格
            facecolor='white',  # 设置背景色为白色
            edgecolor='black',  # 设置边框颜色为黑色
            rc={'axes.labelcolor': 'gray'}  # 设置标签颜色为灰色
        )

        "Figure对象表示整个图表，Axes对象是一个包含多个子图表的容器"
        self.fig, self.axlist = mpf.plot(df, style=my_style, type='candle',mav=(5,10, 20), volume=True, show_nontrading=False, returnfig=True)
        canvas = FigureCanvasTkAgg(self.fig, master=self.stock_graphics)  # 设置tkinter绘制区
        if len(self.stock_graphics.winfo_children()) == 2:     # 如果子元素数量不为 2，那么说明还没有绘制过图形，不需要进行销毁操作。
            self.stock_graphics.winfo_children()[0].destroy()
        canvas.draw()  # 使用Canvas的draw()方法将图形绘制到Canvas上
        canvas._tkcanvas.pack(side='right')  # Tkinter的pack()方法将Canvas添加到Frame中。

# 最开始的登录界面
class LoginWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Login Window")
        self.geometry("450x200+550+175")
        self.resizable(False, False)

        tk.Label(self, text="Username:").grid(row=0, column=0, padx=10, pady=10)
        self.username_entry = tk.Entry(self)
        self.username_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(self, text="Password:").grid(row=2, column=0, padx=10, pady=10)
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.grid(row=2, column=1, padx=10, pady=10)

        self.login_button = tk.Button(self, text="Login", command=self.login)
        self.login_button.grid(row=4, column=1, padx=10, pady=10)
        self.info=tk.Label(self, text="")
        #self.info.grid(row=4, column=0, padx=5, pady=5)
        self.parent = parent

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username == "name" and password == "pass":  # 如果相同，销毁当前的窗口（即登录窗口），显示上一级窗口
            self.destroy()
            self.parent.deiconify()
        else:
            tk.messagebox.showerror("Error", "Invalid username or password")


# 为K线图读取数据

def get_data():
    global choice, flag
    symbol=""
    if flag==2:
        symbol='FUSHIDA'
    elif flag==1:
        symbol='AAPL'
    elif flag==3:
        symbol='GELIDIANQI'
    data = findall_data(symbol)
    # 列表  列名
    colsname = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    # 临时数据文件名
    datafile = 'temp.csv'
    # 写入数据到临时数据文件
    # start
    with open(datafile, 'w', newline='', encoding='GBK') as wf:
        writer = csv.writer(wf)
        writer.writerow(colsname)
        for quotes in data:
            row = [quotes['Date'], quotes['Open'], quotes['High'],
                   quotes['Low'], quotes['Close'], quotes['Volume']]
            writer.writerow(row)
        # end

    # 此时的数据，才满足mplfinance的数据的使用规范
    df = pd.read_csv(datafile)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index(['Date'], inplace=True)
    return df

def ConfigTable(table,canvas,scrollbar):
    tk.Button(table, text='Date', width=20, height=1).grid(row=0, column=0, padx=10)
    tk.Button(table, text='Open', width=12, height=1).grid(row=0, column=1)
    tk.Button(table, text='High', width=12, height=1).grid(row=0, column=2)
    tk.Button(table, text='Low', width=12, height=1).grid(row=0, column=3)
    tk.Button(table, text='Close', width=12, height=1).grid(row=0, column=4)
    tk.Button(table, text='Volume', width=12, height=1).grid(row=0, column=5)

    with codecs.open('temp.csv', encoding='utf-8') as f:
        i = 1
        j = 0
        for row in csv.DictReader(f, skipinitialspace=True):
            tk.Button(table, text=str(row['Date']), width=20, height=1).grid(row=i, column=j, padx=10)
            j = j + 1
            tk.Button(table, text=str(row['Open']), width=12, height=1).grid(row=i, column=j)
            j = j + 1
            tk.Button(table, text=str(row['High']), width=12, height=1).grid(row=i, column=j)
            j = j + 1
            tk.Button(table, text=str(row['Low']), width=12, height=1).grid(row=i, column=j)
            j = j + 1
            tk.Button(table, text=str(row['Close']), width=12, height=1).grid(row=i, column=j)
            j = j + 1
            tk.Button(table, text=str(row['Volume']), width=12, height=1).grid(row=i, column=j)
            i = i + 1
            j = 0

    table.pack()

    canvas.place(x=60, y=200)
    scrollbar.pack(side="right", fill="y")

# 创建控制线程对象controlthread
controlthread = threading.Thread(target=controlthread_body, name='ControlThread')
# 启动线程controlthread
controlthread.start()

# 创建工作线程对象workthread
workthread = threading.Thread(target=workthread_body, name='WorkThread')
# 启动线程workthread
workthread.start()

windowthread = threading.Thread(target=creatWindow, name='WindowThread')
windowthread.start()
