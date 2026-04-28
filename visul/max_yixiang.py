import json
import csv
from collections import defaultdict, Counter

def analyze_imagery_frequencies(csv_file_path, json_file_path):
    """
    读取CSV和JSON文件，统计每个二级类别下出现频率最高的6种意象。
    """
    # 1. 解析CSV，建立 意象 -> 二级类别 的映射
    imagery_to_secondary_cat = {}
    
    with open(csv_file_path, mode='r', encoding='utf-8') as f:
        # 如果您的CSV有表头，请取消下面这行的注释以跳过表头
        # next(f) 
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 3:
                imagery_word = row[0].strip()   # 第1列：具体意象 (如 "离愁")
                secondary_cat = row[2].strip()  # 第3列：二级类别 (如 "离别")
                imagery_to_secondary_cat[imagery_word] = secondary_cat

    # 2. 解析JSON，统计各个二级类别下的意象频率
    # 数据结构: { "二级类别": Counter({"意象1": 10, "意象2": 5}) }
    category_counts = defaultdict(Counter)
    
    with open(json_file_path, mode='r', encoding='utf-8') as f:
        poems_data = json.load(f)
        
    for poem in poems_data:
        # 获取该首诗匹配到的意象列表，若无该键则默认为空列表
        matched_imageries = poem.get("matched_imagery", [])
        
        for imagery in matched_imageries:
            # 查找该意象所属的二级类别
            sec_cat = imagery_to_secondary_cat.get(imagery)
            
            # 如果在CSV中找到了对应的二级类别，则进行频次累加
            if sec_cat:
                category_counts[sec_cat][imagery] += 1

    # 3. 提取每个二级类别下的前6名意象
    results = {}
    for sec_cat, counts in category_counts.items():
        # most_common(6) 返回列表中出现次数最多的6个元素及其出现次数
        # 格式为: [('意象A', 50), ('意象B', 30), ...]
        top_6 = counts.most_common(6)
        results[sec_cat] = top_6
        
    return results

if __name__ == "__main__":
    # ---------------- 配置输入文件路径 ----------------
    # 请将其修改为您本地的实际文件路径
    CSV_PATH = r'yixiang.csv '
    JSON_PATH = r'poem_time_visual.json '
    # --------------------------------------------------

    try:
        top_imageries_by_category = analyze_imagery_frequencies(CSV_PATH, JSON_PATH)
        
        # 格式化输出结果
        print("====== 意象统计结果 ======\n")
        for category, imageries in top_imageries_by_category.items():
            print(f"【二级类别: {category}】")
            for rank, (imagery, count) in enumerate(imageries, start=1):
                print(f"  {rank}. {imagery} (频次: {count})")
            print("-" * 30)
            
    except FileNotFoundError as e:
        print(f"文件读取错误: {e}。请确保文件路径正确。")
    except json.JSONDecodeError:
        print("JSON解析错误。请确保JSON文件格式合法。")
    except Exception as e:
        print(f"执行过程中发生错误: {e}")