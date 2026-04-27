import json
import re
from collections import defaultdict, Counter


POEMS_PATH = r'30shi\rsimplified_poems.json'
IMAGERY_PATH = r'yixiang.txt'
OUTPUT_PATH = "sampled_1000_imagery_poems.json"

TARGET_TOTAL = 1000
MIN_PER_AUTHOR = 10   # 每位诗人至少保留多少首，可改成 20、30


def load_poems(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_imagery_words(path):
    words = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            # 支持一行多个词：月 山 水 / 月,山,水 / 月，山，水
            parts = re.split(r"[,\s，、]+", line)

            for p in parts:
                p = p.strip()
                if p:
                    words.append(p)

    # 去重，并按长度降序，避免“山水”被“山”“水”干扰
    words = sorted(set(words), key=len, reverse=True)
    return words


def poem_text(poem):
    title = poem.get("title", "")
    paragraphs = poem.get("paragraphs", [])
    body = "".join(paragraphs)
    return title + body


def score_poem(poem, imagery_words):
    text = poem_text(poem)
    text_length = len(text)

    matched_words = []
    total_count = 0

    for word in imagery_words:
        count = text.count(word)
        if count > 0:
            matched_words.append(word)
            total_count += count

    unique_count = len(matched_words)

    if text_length == 0:
        density = 0
    else:
        # 每100字中包含多少种不同意象
        density = unique_count / text_length * 100

    # 评分规则：
    # 主要看意象密度，其次看不同意象数量，最后看总出现次数
    score = density * 100 + unique_count * 2 + total_count * 0.5

    return {
        "score": score,
        "unique_imagery_count": unique_count,
        "total_imagery_count": total_count,
        "imagery_density": density,
        "text_length": text_length,
        "matched_imagery": matched_words
    }

def add_scores(poems, imagery_words):
    scored_poems = []

    for poem in poems:
        info = score_poem(poem, imagery_words)

        new_poem = dict(poem)
        new_poem["imagery_score"] = info["score"]
        new_poem["unique_imagery_count"] = info["unique_imagery_count"]
        new_poem["total_imagery_count"] = info["total_imagery_count"]
        new_poem["matched_imagery"] = info["matched_imagery"]
        new_poem["imagery_density"] = info["imagery_density"]
        new_poem["text_length"] = info["text_length"]

        scored_poems.append(new_poem)

    return scored_poems


def sample_with_author_balance(scored_poems, target_total=1000, min_per_author=10):
    author_dict = defaultdict(list)

    for poem in scored_poems:
        author = poem.get("author", "未知作者")
        author_dict[author].append(poem)

    # 每个作者内部按意象分数排序
    for author in author_dict:
        author_dict[author].sort(
            key=lambda x: (
                 x["imagery_score"],
                 x["imagery_density"],
                 x["unique_imagery_count"],
                 x["total_imagery_count"]
                ),
            reverse=True
        )

    selected = []
    selected_ids = set()

    # 第一步：每位作者先取 min_per_author 首
    for author, plist in author_dict.items():
        take_n = min(min_per_author, len(plist))

        for poem in plist[:take_n]:
            selected.append(poem)
            selected_ids.add(poem["id"])

    # 第二步：剩余名额按全局意象分数补齐
    remaining_candidates = [
        poem for poem in scored_poems
        if poem["id"] not in selected_ids
    ]

    remaining_candidates.sort(
        key=lambda x: (
            x["imagery_score"],
            x["unique_imagery_count"],
            x["total_imagery_count"],
            len(poem_text(x))
        ),
        reverse=True
    )

    need = target_total - len(selected)

    if need > 0:
        selected.extend(remaining_candidates[:need])

    # 如果超过目标数量，整体再按分数截断
    selected = sorted(
        selected,
        key=lambda x: (
            x["imagery_score"],
            x["unique_imagery_count"],
            x["total_imagery_count"],
            len(poem_text(x))
        ),
        reverse=True
    )[:target_total]

    return selected


def print_report(sampled_poems):
    print("=" * 40)
    print(f"最终抽样数量：{len(sampled_poems)}")

    author_counter = Counter(p.get("author", "未知作者") for p in sampled_poems)

    print("\n各诗人抽样数量：")
    for author, count in author_counter.most_common():
        print(f"{author}: {count}")

    print("\n意象得分最高的前10首：")
    for p in sampled_poems[:10]:
        print(
            f"{p.get('author')}《{p.get('title')}》 "
            f"score={p['imagery_score']} "
            f"unique={p['unique_imagery_count']} "
            f"total={p['total_imagery_count']} "
            f"imagery={p['matched_imagery'][:10]}"
        )


def main():
    poems = load_poems(POEMS_PATH)
    imagery_words = load_imagery_words(IMAGERY_PATH)

    print(f"读取诗歌数量：{len(poems)}")
    print(f"读取意象词数量：{len(imagery_words)}")

    scored_poems = add_scores(poems, imagery_words)

    sampled_poems = sample_with_author_balance(
        scored_poems,
        target_total=TARGET_TOTAL,
        min_per_author=MIN_PER_AUTHOR
    )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(sampled_poems, f, ensure_ascii=False, indent=2)

    print_report(sampled_poems)

    print(f"\n已保存到：{OUTPUT_PATH}")


if __name__ == "__main__":
    main()