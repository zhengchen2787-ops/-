import json
import re
from collections import Counter
from itertools import combinations


POEMS_PATH = r'sampled_1000_imagery_poems.json'
IMAGERY_PATH = r'yixiang.txt'
OUTPUT_PATH = "co_occurrence.json"


# ========= 1. 读取意象词 =========
def load_imagery_words(path):
    words = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parts = re.split(r"[,\s，、]+", line.strip())
            for p in parts:
                if p:
                    words.append(p)

    # 去重 + 按长度排序（关键！先匹配长词）
    words = sorted(set(words), key=len, reverse=True)

    return words


# ========= 2. 构建“归一化词典” =========
def build_normalization_map(words):
    """
    把“白云→云”“青草→草”
    规则：短词是长词的子串 → 归一到短词
    """
    norm_map = {}

    sorted_words = sorted(words, key=len)  # 短词在前

    for w in words:
        norm_map[w] = w  # 默认自己

        for base in sorted_words:
            if base == w:
                continue

            if base in w:
                norm_map[w] = base
                break

    return norm_map


# ========= 3. 提取诗中意象 =========
def extract_imagery(text, imagery_words):
    found = set()

    for w in imagery_words:
        if w in text:
            found.add(w)

    return found


# ========= 4. 主逻辑 =========
def build_co_occurrence(poems, imagery_words, norm_map):
    pair_counter = Counter()

    for poem in poems:
        text = "".join(poem.get("paragraphs", []))

        # 提取意象
        raw_words = extract_imagery(text, imagery_words)

        # 🔥 归一化（关键步骤）
        normalized = set()
        for w in raw_words:
            normalized.add(norm_map.get(w, w))

        # 再去重（防止 云 + 白云）
        normalized = list(normalized)

        # 共现统计
        for a, b in combinations(sorted(normalized), 2):
            pair_counter[(a, b)] += 1

    # 转为前端格式
    result = [
        {"source": a, "target": b, "value": count}
        for (a, b), count in pair_counter.items()
    ]

    # 按强度排序
    result.sort(key=lambda x: x["value"], reverse=True)

    return result


# ========= 5. 运行 =========
def main():
    # 读诗
    with open(POEMS_PATH, "r", encoding="utf-8") as f:
        poems = json.load(f)

    # 读意象
    imagery_words = load_imagery_words(IMAGERY_PATH)

    print(f"意象词数量: {len(imagery_words)}")

    # 构建归一化
    norm_map = build_normalization_map(imagery_words)

    # 共现统计
    co_occurrence = build_co_occurrence(poems, imagery_words, norm_map)

    # 保存
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(co_occurrence, f, ensure_ascii=False, indent=2)

    print(f"完成，共 {len(co_occurrence)} 条共现关系")


if __name__ == "__main__":
    main()