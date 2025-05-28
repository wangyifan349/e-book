import sys
import re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QSplitter, QListWidget, QTextEdit, QLineEdit,
    QComboBox, QVBoxLayout, QHBoxLayout, QLabel, QListWidgetItem,
    QMessageBox, QPushButton, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette

# ------------------- 电子书加载与处理函数 --------------------

# 读取电子书文件，按一级标题（#开头）分章，返回章节列表
def load_pages(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # 使用正则按标题拆分，内容紧跟标题后面
    parts = re.split(r'(^# .*)', text, flags=re.MULTILINE)
    pages = []
    i = 1  # 标题索引开始
    while i < len(parts):
        title = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ''
        pages.append({'title': title, 'content': content})
        i += 2  # 跳到下一标题
    return pages

# 计算字符串a和b的最长公共子序列长度（LCS），返回整数长度
def lcs_length(a, b):
    m, n = len(a), len(b)
    dp = []
    i = 0
    # 初始化二维动态规划矩阵，大小(m+1)*(n+1)，全部0
    while i <= m:
        row = []
        j = 0
        while j <= n:
            row.append(0)
            j += 1
        dp.append(row)
        i += 1
    # 计算最长公共子序列长度 dp
    i = 0
    while i < m:
        j = 0
        while j < n:
            if a[i] == b[j]:
                dp[i + 1][j + 1] = dp[i][j] + 1
            else:
                dp[i + 1][j + 1] = max(dp[i][j + 1], dp[i + 1][j])
            j += 1
        i += 1
    return dp[m][n]  # 返回矩阵右下角值，即LCS长度

# 计算a,b字符串的LCS相似度，范围0~1
def similarity_lcs(a, b):
    a, b = a.lower(), b.lower()
    lcs = lcs_length(a, b)
    max_len = max(len(a), len(b))
    if max_len == 0:
        return 0.0
    return lcs / float(max_len)  # LCS长度除以较长字符串长度，表示相似度

# 计算a,b字符串的莱文斯坦编辑距离
def levenshtein_distance(a, b):
    m, n = len(a), len(b)
    dp = []
    i = 0
    # 初始化二维动态规划矩阵，大小(m+1)*(n+1)
    while i <= m:
        dp.append([0] * (n + 1))
        i += 1
    # 边界初始化：空串转化代价
    i = 0
    while i <= m:
        dp[i][0] = i
        i += 1
    j = 0
    while j <= n:
        dp[0][j] = j
        j += 1
    # 动态规划计算编辑距离
    i = 1
    while i <= m:
        j = 1
        while j <= n:
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,          # 删除
                dp[i][j - 1] + 1,          # 插入
                dp[i - 1][j - 1] + cost    # 替换
            )
            j += 1
        i += 1
    return dp[m][n]  # 返回编辑距离

# 计算莱文斯坦相似度，1 - (编辑距离 / 最大长度)
def similarity_levenshtein(a, b):
    a, b = a.lower(), b.lower()
    dist = levenshtein_distance(a, b)
    max_len = max(len(a), len(b))
    if max_len == 0:
        return 0.0
    return 1.0 - dist / max_len

# ------------------- 搜索线程 --------------------

# 独立线程进行关键词模糊搜索，避免UI卡顿
class SearchThread(QThread):
    # 信号：搜索完成传回结果list
    results_ready = pyqtSignal(list)

    # 初始化传入页面列表，关键词，算法函数，相似度阈值
    def __init__(self, pages, keyword, sim_func, threshold=0.5):
        super().__init__()
        self.pages = pages
        self.keyword = keyword
        self.sim_func = sim_func
        self.threshold = threshold

    # 线程执行搜索逻辑
    def run(self):
        result = []
        i = 0
        while i < len(self.pages):
            sim = self.sim_func(self.pages[i]['title'], self.keyword)
            if sim >= self.threshold:
                result.append(self.pages[i])
            i += 1
        self.results_ready.emit(result)

# ------------------- 主窗口类 --------------------

class EbookViewer(QWidget):

    # 初始化主窗口，加载电子书，搭建UI
    def __init__(self):
        super().__init__()

        # 窗口标题和大小
        self.setWindowTitle("电子书在线查看器 - 护眼模式 🌙")
        self.resize(900, 600)

        # 读取电子书数据，失败提示
        try:
            self.pages = load_pages('ebook.txt')
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载 ebook.txt 文件：{e}")
            self.pages = []

        self.filtered_pages = self.pages  # 初始化显示所有章节

        # 左侧目录列表，点击触发内容显示
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.display_content)
        # 设置目录护眼风格CSS
        self.list_widget.setStyleSheet(
            "QListWidget { background-color: #2E3440; color: #D8DEE9; font-size: 14px; }"
            "QListWidget::item:selected { background-color: #81A1C1; color: black; }"
        )

        # 右侧内容区域，只读文本框，字体Consolas，护眼背景色
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Consolas", 11))
        self.text_edit.setStyleSheet("QTextEdit { background-color: #3B4252; color: #D8DEE9; }")

        # 顶部搜索控件及算法选择控件
        self.label_search = QLabel("搜索标题：")
        self.label_search.setStyleSheet("color: #D8DEE9; font-weight: bold;")
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("输入关键词，点击搜索按钮或按回车")
        self.input_search.setStyleSheet(
            "QLineEdit { background-color: #4C566A; color: #ECEFF4; border-radius: 4px; padding: 4px; }"
        )
        self.input_search.returnPressed.connect(self.on_search_clicked)

        self.combo_algo = QComboBox()
        self.combo_algo.addItem("最长公共子序列 (LCS)")
        self.combo_algo.addItem("编辑距离 (Levenshtein)")
        self.combo_algo.setStyleSheet(
            "QComboBox { background-color: #4C566A; color: #ECEFF4; border-radius: 4px; padding: 2px 6px; }"
        )

        self.btn_search = QPushButton("搜索")
        self.btn_search.setStyleSheet(
            "QPushButton { background-color: #5E81AC; color: white; border-radius: 4px; padding: 6px 12px; }"
            "QPushButton:hover { background-color: #81A1C1; }"
            "QPushButton:pressed { background-color: #4C566A; }"
            "QPushButton:disabled { background-color: #434C5E; }"
        )
        self.btn_search.clicked.connect(self.on_search_clicked)

        # 打开文件按钮，点击弹出文件选择对话框
        self.btn_open = QPushButton("打开电子书文件")
        self.btn_open.setStyleSheet(
            "QPushButton { background-color: #A3BE8C; color: black; border-radius: 4px; padding: 6px 12px; }"
            "QPushButton:hover { background-color: #B5CF9D; }"
            "QPushButton:pressed { background-color: #8AA265; }"
        )
        self.btn_open.clicked.connect(self.open_ebook_file)

        # 顶部横向布局，包含搜索标签、输入框、算法选择、搜索按钮和打开文件按钮
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.label_search)
        top_layout.addWidget(self.input_search)
        top_layout.addWidget(QLabel("算法选择："))
        top_layout.addWidget(self.combo_algo)
        top_layout.addWidget(self.btn_search)
        top_layout.addWidget(self.btn_open)

        # 设置整体暗色背景
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#2E3440"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # 水平分割器，左侧目录右侧文本
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.list_widget)
        splitter.addWidget(self.text_edit)
        splitter.setStretchFactor(0, 1)  # 左侧占比
        splitter.setStretchFactor(1, 3)  # 右侧占比

        # 窗口主布局，垂直，先上面搜索栏再分割器
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        # 设置顶部全部标签字体颜色，略带淡色对比
        top_widget_color = "#D8DEE9"
        self.setStyleSheet(f"QLabel {{ color: {top_widget_color}; font-size: 14px; }}")

        # 显示原始全部章节目录
        self.update_list()

        # 搜索线程实例，防止多线程冲突
        self.search_thread = None

    # 更新目录列表显示：清空并加入当前过滤后的章节标题
    def update_list(self):
        self.list_widget.clear()
        i = 0
        while i < len(self.filtered_pages):
            item = QListWidgetItem(self.filtered_pages[i]['title'])
            self.list_widget.addItem(item)
            i += 1
        self.text_edit.clear()  # 新目录不显示内容，需点击显示

    # 点击目录条目时显示对应章节内容
    def display_content(self, item):
        title = item.text()
        i = 0
        # 遍历当前过滤章节，查找匹配标题
        while i < len(self.filtered_pages):
            if self.filtered_pages[i]['title'] == title:
                content = self.filtered_pages[i]['content']
                break
            i += 1
        else:
            content = ''
        # 文本窗口显示内容
        self.text_edit.setPlainText(content)

    # 搜索按钮或回车触发的函数，启动线程搜索
    def on_search_clicked(self):
        keyword = self.input_search.text().strip()
        if keyword == '':
            # 关键词为空，恢复显示全部章节目录
            self.filtered_pages = self.pages
            self.update_list()
            return

        # 选择相似度算法函数
        choice = self.combo_algo.currentIndex()
        if choice == 0:
            sim_func = similarity_lcs
        else:
            sim_func = similarity_levenshtein

        # 如果已有搜索线程运行，忽略此次点击
        if self.search_thread is not None and self.search_thread.isRunning():
            return

        # 禁用搜索按钮，防止重复启动
        self.btn_search.setEnabled(False)

        # 清空目录，文本区显示“搜索中”
        self.list_widget.clear()
        self.text_edit.setPlainText("搜索中，请稍候...")

        # 创建并启动搜索线程
        self.search_thread = SearchThread(self.pages, keyword, sim_func, threshold=0.5)
        self.search_thread.results_ready.connect(self.on_search_finished)
        self.search_thread.start()

    # 搜索线程完成回调，更新UI显示结果
    def on_search_finished(self, results):
        self.filtered_pages = results
        if len(results) == 0:
            QMessageBox.information(self, "提示", "未找到匹配章节。")
            self.text_edit.clear()
        self.update_list()
        self.btn_search.setEnabled(True)  # 重新启用搜索按钮
        self.search_thread = None  # 清空线程引用

    # 打开文件按钮点击，弹出文件选择对话框并加载文件
    def open_ebook_file(self):
        # 弹出文件对话框，只显示txt文件
        file_path, _ = QFileDialog.getOpenFileName(self, "打开电子书文件", "", "文本文件 (*.txt);;所有文件 (*)")
        if not file_path:
            return  # 未选文件时直接返回

        try:
            # 加载电子书，解析章节
            new_pages = load_pages(file_path)
            if not new_pages:
                QMessageBox.warning(self, "提醒", "该文件没有检测到有效章节，确认格式正确！")
                return
            self.pages = new_pages
            self.filtered_pages = self.pages
            self.update_list()
            self.text_edit.clear()
            self.input_search.clear()
            QMessageBox.information(self, "成功", f"成功加载电子书文件：{file_path}")
            self.setWindowTitle(f"电子书在线查看器 - 护眼模式 🌙 - {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载文件失败：{e}")

# ------------------- 程序入口 --------------------

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 统一美观风格
    viewer = EbookViewer()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
