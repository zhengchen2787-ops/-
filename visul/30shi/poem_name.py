import json
from collections import defaultdict

# 1. 读取你的 JSON 文件
input_file = r'30shi\rsimplified_poems.json'
output_file = 'llm_prompt_input.txt'

with open(input_file, 'r', encoding='utf-8') as f:
    poems_data = json.load(f)

# 2. 使用 defaultdict 聚合相同诗人的诗歌题目
# 结构类似于: {'李贺': ['鼓吹曲辞 艾如张', '马诗二十三首', ...], '卢照邻': [...]}
author_titles = defaultdict(list)

for poem in poems_data:
    author = poem.get('author', '未知')
    title = poem.get('title', '无题')
    author_titles[author].append(title)

# 3. 准备输出给大模型的文本
output_lines = []

# 写一个绝佳的 Prompt 头，直接指导大模型如何输出
prompt_header = """
你是一个精通中国古典文学的数字人文专家。
我正在构建一个唐诗时空可视化系统，需要为以下诗人和作品补充时间元数据。


请以严格的 JSON 格式返回给我，格式参考如下：
{
  "李贺": {"era": "中唐", "active_years": "790-816", "notable_poems_time": {"鼓吹曲辞 艾如张": "约810年"}},
  ...
}

以下是需要补充数据的诗人及作品列表：
==================================================
"""
output_lines.append(prompt_header)

# 4. 遍历字典，格式化输出
for author, titles in author_titles.items():
    output_lines.append(f"【诗人】：{author}")
    
    # 去重并截取前 20 首（防止 Token 爆炸，大模型看几首代表作就能定年代了）
    unique_titles = list(set(titles))
    sampled_titles = unique_titles[:20] 
    
    output_lines.append(f"包含作品（截取展示）：{', '.join(sampled_titles)}")
    output_lines.append("-" * 40)

# 5. 写入文件
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("\n".join(output_lines))

print(f"提取完成！一共聚合了 {len(author_titles)} 位诗人。")
print(f"请打开 {output_file}，将里面的内容复制发送给大语言模型即可。")