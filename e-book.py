import re   # 引入正则模块，用于文本分割

# --------------------------------------------------------------------------------
# 定义函数 - 读取电子书文件，并按一级标题分割内容，返回页列表
def load_pages(filepath):
    f = open(filepath, 'r', encoding='utf-8')    # 以utf-8编码打开电子书文本文件
    text = f.read()                               # 读取全部文本内容
    f.close()                                     # 关闭文件

    # 用正则分割文本，以从新行开始的 "# " 开头行作为标题分割点
    parts = re.split(r'(^# .*)', text, flags=re.MULTILINE)

    pages = []         # 初始化保存章节页的列表
    i = 1              # 从索引1开始，因为分割结果中偶数索引一般为内容，奇数索引为标题
    while i < len(parts):                      # 遍历所有标题和内容对
        title = parts[i].strip()               # 当前索引为标题，去除首尾空白
        if (i + 1) < len(parts):               # 判断是否有对应内容文本
            content = parts[i + 1].strip()     # 有则取出并去空白
        else:
            content = ''                       # 没有内容则设为空字符串
        pages.append({'title': title, 'content': content})   # 添加字典保存标题和内容
        i = i + 2                            # 步进2，跳到下一个标题
    return pages                            # 返回所有章节页列表

# --------------------------------------------------------------------------------
# 定义函数 - 计算两个字符串的最长公共子序列长度
def lcs_length(a, b):
    m = len(a)    # 获取字符串a长度
    n = len(b)    # 获取字符串b长度

    dp = []       # 初始化二维数组（列表的列表），用来存储子问题结果
    i = 0
    while i <= m:
        row = []  # 当前行为空列表
        j = 0
        while j <= n:
            row.append(0)    # 每列初始化为0
            j += 1          # 列索引+1
        dp.append(row)      # 把当前行添加到dp数组
        i += 1              # 行索引+1

    i = 0
    while i < m:
        j = 0
        while j < n:
            if a[i] == b[j]:                # 如果当前两个字符相等
                dp[i + 1][j + 1] = dp[i][j] + 1   # 状态转移，匹配长度+1
            else:
                # 取左边或上边较大值，保证最长长度
                if dp[i][j + 1] > dp[i + 1][j]:
                    dp[i + 1][j + 1] = dp[i][j + 1]
                else:
                    dp[i + 1][j + 1] = dp[i + 1][j]
            j += 1        # 列索引+1
        i += 1            # 行索引+1

    return dp[m][n]       # 返回LCS长度（右下角元素）

# --------------------------------------------------------------------------------
# 定义函数 - 计算两个字符串基于LCS的相似度，返回0~1浮点数
def similarity_lcs(a, b):
    a = a.lower()                  # 全部转为小写，忽略大小写差异
    b = b.lower()                  # 同上
    lcs = lcs_length(a, b)         # 调用LCS长度函数
    max_len = max(len(a), len(b))  # 取两字符串长度最大值
    if max_len == 0:               # 防止除0错误，两个空字符串相似度为0
        return 0.0
    return lcs / float(max_len)    # 相似度 = LCS长度 / 最大字符串长度

# --------------------------------------------------------------------------------
# 定义函数 - 计算两个字符串的莱文斯坦编辑距离
def levenshtein_distance(a, b):
    m = len(a)    # a字符串长度
    n = len(b)    # b字符串长度

    dp = []       # 初始化二维数组，存储编辑距离状态
    i = 0
    while i <= m:
        row = []
        j = 0
        while j <= n:
            row.append(0)
            j += 1
        dp.append(row)
        i += 1

    i = 0
    while i <= m:
        dp[i][0] = i        # 空字符串变换为首i个字符所需删除操作数
        i += 1
    j = 0
    while j <= n:
        dp[0][j] = j        # 空字符串变换为首j个字符所需插入操作数
        j += 1

    i = 1
    while i <= m:
        j = 1
        while j <= n:
            if a[i - 1] == b[j - 1]:   # 字符相等无替换代价
                cost = 0
            else:
                cost = 1               # 字符不等则替换代价为1

            deletion = dp[i - 1][j] + 1       # 删除操作代价
            insertion = dp[i][j - 1] + 1      # 插入操作代价
            substitution = dp[i - 1][j - 1] + cost  # 替换操作代价

            min_cost = deletion               # 先假设删除为最小
            if insertion < min_cost:          # 比较插入
                min_cost = insertion
            if substitution < min_cost:      # 比较替换
                min_cost = substitution

            dp[i][j] = min_cost               # 选三者中最小代价
            j += 1
        i += 1

    return dp[m][n]        # 返回字符串间编辑距离

# --------------------------------------------------------------------------------
# 定义函数 - 根据编辑距离计算相似度，0~1浮点数
def similarity_levenshtein(a, b):
    a = a.lower()           # 转小写
    b = b.lower()           # 转小写
    dist = levenshtein_distance(a, b)  # 计算编辑距离
    max_len = max(len(a), len(b))       # 最大字符串长度
    if max_len == 0:         # 防止除0
        return 0.0
    return 1.0 - (float(dist) / max_len)   # 相似度=1-距离/最大长度

# --------------------------------------------------------------------------------
# 定义函数 - 使用传入的相似度函数，匹配标题搜索，返回相似度大于阈值的页列表
def search_by_title(pages, keyword, similarity_func, threshold):
    results = []              # 保存匹配结果的列表
    i = 0
    while i < len(pages):        # 遍历每一页
        sim = similarity_func(pages[i]['title'], keyword)   # 计算相似度
        if sim >= threshold:                               # 如果大于阈值
            results.append(pages[i])                        # 加入结果
        i += 1
    return results

# --------------------------------------------------------------------------------
# 主程序开始

filename = 'ebook.txt'               # 电子书文件名（需自行准备好）
pages = load_pages(filename)         # 加载电子书内容，得到页列表

print("请选择搜索算法（输入数字）：")
print("1. 最长公共子序列相似度")
print("2. 编辑距离相似度")

algo_choice = ''    # 初始化选择变量

# 循环直到获取正确选择
while algo_choice != '1' and algo_choice != '2':
    algo_choice = input("请输入选择（1 或 2）：").strip()  # 读取输入并去除空白

if algo_choice == '1':            # 选择LCS算法
    sim_func = similarity_lcs
else:                            # 否则选择编辑距离算法
    sim_func = similarity_levenshtein
threshold = 0.5    # 设定相似度阈值，也可以扩展让用户输入
print("输入关键词进行搜索，直接回车退出程序。")
# 无限循环，实现持续搜素功能
while True:
    print()                         # 空行分隔
    keyword = input("请输入搜索关键词：")   # 读取用户关键词

    if keyword.strip() == '':       # 如果输入为空，退出循环结束程序
        print("退出程序。")
        break
    matches = search_by_title(pages, keyword, sim_func, threshold)   # 搜索匹配页
    if len(matches) == 0:           # 没找到匹配
        print("未找到相关内容。")
    else:
        i = 0
        while i < len(matches):     # 打印所有匹配结果
            print(matches[i]['title'])
            print(matches[i]['content'])
            print('-' * 40)        # 分割线
            i += 1
