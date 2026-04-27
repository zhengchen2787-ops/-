import json
from collections import defaultdict, Counter


INPUT_PATH = "poem_time_visual.json"

OUT_LONG = "timeline_year_imagery_long.json"
OUT_WIDE = "timeline_year_imagery_wide.json"
OUT_SUMMARY = "timeline_year_summary.json"

START_YEAR = 648
END_YEAR = 907

# 统计方式：
# "spread"：区间均摊，推荐。例如 year_range=[720,729]，每年 +0.1
# "full"：区间内每年都 +1，不推荐，容易放大区间诗
# "middle"：只算 estimated_year 那一年
COUNT_MODE = "spread"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def clean_imagery_list(words):
    """
    同一首诗里，同一个意象只算一次。
    例如 matched_imagery = ["云", "白云", "云"]，
    如果你已经在前面 normalize 过，这里会去重。
    """
    if not words:
        return []

    result = []
    for w in words:
        if not w:
            continue
        w = str(w).strip()
        if w:
            result.append(w)

    return sorted(set(result))


def get_years_for_poem(poem):
    """
    根据 COUNT_MODE 返回这首诗应该计入哪些年份，以及每年的权重。
    """

    estimated_year = poem.get("estimated_year")
    year_range = poem.get("year_range")

    # 优先使用 year_range
    if isinstance(year_range, list) and len(year_range) == 2:
        start, end = year_range

        if isinstance(start, int) and isinstance(end, int):
            # 限制在 648-907
            start = max(start, START_YEAR)
            end = min(end, END_YEAR)

            if start > end:
                return []

            if COUNT_MODE == "spread":
                years = list(range(start, end + 1))
                weight = 1 / len(years)
                return [(y, weight) for y in years]

            elif COUNT_MODE == "full":
                return [(y, 1) for y in range(start, end + 1)]

            elif COUNT_MODE == "middle":
                mid = round((start + end) / 2)
                if START_YEAR <= mid <= END_YEAR:
                    return [(mid, 1)]

    # 如果没有 year_range，再使用 estimated_year
    if isinstance(estimated_year, int):
        if START_YEAR <= estimated_year <= END_YEAR:
            return [(estimated_year, 1)]

    return []


def build_yearly_imagery_stats(poems):
    """
    year_imagery_counter:
    {
      720: {"云": 1.3, "月": 2.1},
      721: {"云": 0.8}
    }
    """

    year_imagery_counter = {
        year: defaultdict(float)
        for year in range(START_YEAR, END_YEAR + 1)
    }

    year_poem_counter = defaultdict(float)
    year_real_poem_counter = defaultdict(int)

    unmatched_poems = []

    for poem in poems:
        imagery_list = clean_imagery_list(poem.get("matched_imagery", []))
        year_weights = get_years_for_poem(poem)

        if not imagery_list or not year_weights:
            unmatched_poems.append({
                "id": poem.get("id"),
                "title": poem.get("title"),
                "author": poem.get("author"),
                "estimated_year": poem.get("estimated_year"),
                "year_range": poem.get("year_range"),
                "matched_imagery": poem.get("matched_imagery", [])
            })
            continue

        for year, weight in year_weights:
            year_poem_counter[year] += weight

            for imagery in imagery_list:
                year_imagery_counter[year][imagery] += weight

        # 这个是未加权的“涉及年份诗歌数”，只用于检查
        for year, _ in year_weights:
            year_real_poem_counter[year] += 1

    return year_imagery_counter, year_poem_counter, year_real_poem_counter, unmatched_poems


def to_long_format(year_imagery_counter):
    """
    输出：
    [
      {"year": 720, "imagery": "云", "value": 1.2},
      {"year": 720, "imagery": "月", "value": 0.5}
    ]
    """

    result = []

    for year in range(START_YEAR, END_YEAR + 1):
        counter = year_imagery_counter[year]

        for imagery, value in counter.items():
            if value <= 0:
                continue

            result.append({
                "year": year,
                "imagery": imagery,
                "value": round(value, 4)
            })

    result.sort(key=lambda x: (x["year"], -x["value"], x["imagery"]))
    return result


def to_wide_format(year_imagery_counter):
    """
    输出：
    [
      {"year": 648, "云": 0, "月": 1.2, ...},
      {"year": 649, "云": 0.3, "月": 0, ...}
    ]
    """

    all_imagery = sorted({
        imagery
        for counter in year_imagery_counter.values()
        for imagery in counter.keys()
    })

    result = []

    for year in range(START_YEAR, END_YEAR + 1):
        row = {"year": year}

        for imagery in all_imagery:
            row[imagery] = round(year_imagery_counter[year].get(imagery, 0), 4)

        result.append(row)

    return result


def build_summary(year_imagery_counter, year_poem_counter, year_real_poem_counter):
    """
    每年总览，用于检查抽样是否不均衡。
    """

    result = []

    for year in range(START_YEAR, END_YEAR + 1):
        counter = year_imagery_counter[year]
        total_imagery_mentions = sum(counter.values())

        top_imagery = sorted(
            counter.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        result.append({
            "year": year,
            "weighted_poem_count": round(year_poem_counter.get(year, 0), 4),
            "raw_poem_count_touching_year": year_real_poem_counter.get(year, 0),
            "total_imagery_mentions": round(total_imagery_mentions, 4),
            "top_imagery": [
                {
                    "imagery": imagery,
                    "value": round(value, 4)
                }
                for imagery, value in top_imagery
            ]
        })

    return result


def print_report(long_data, summary, unmatched_poems):
    print("=" * 60)
    print(f"统计年份范围：{START_YEAR}-{END_YEAR}")
    print(f"统计模式：{COUNT_MODE}")
    print(f"长表记录数：{len(long_data)}")
    print(f"无法统计的诗歌数：{len(unmatched_poems)}")

    active_years = [
        item for item in summary
        if item["total_imagery_mentions"] > 0
    ]

    print(f"有意象统计的年份数：{len(active_years)}")

    print("\n意象提及最多的前10个年份：")
    top_years = sorted(
        active_years,
        key=lambda x: x["total_imagery_mentions"],
        reverse=True
    )[:10]

    for item in top_years:
        top_words = "、".join(
            f"{d['imagery']}({d['value']})"
            for d in item["top_imagery"][:5]
        )
        print(
            f"{item['year']}年 | "
            f"意象总量={item['total_imagery_mentions']} | "
            f"加权诗数={item['weighted_poem_count']} | "
            f"Top: {top_words}"
        )

    if unmatched_poems:
        print("\n无法统计的前10首：")
        for p in unmatched_poems[:10]:
            print(f"{p.get('author')}《{p.get('title')}》 year_range={p.get('year_range')} imagery={p.get('matched_imagery')}")


def main():
    poems = load_json(INPUT_PATH)

    (
        year_imagery_counter,
        year_poem_counter,
        year_real_poem_counter,
        unmatched_poems
    ) = build_yearly_imagery_stats(poems)

    long_data = to_long_format(year_imagery_counter)
    wide_data = to_wide_format(year_imagery_counter)
    summary = build_summary(
        year_imagery_counter,
        year_poem_counter,
        year_real_poem_counter
    )

    save_json(long_data, OUT_LONG)
    save_json(wide_data, OUT_WIDE)
    save_json(summary, OUT_SUMMARY)

    save_json(unmatched_poems, "unmatched_yearly_poems.json")

    print_report(long_data, summary, unmatched_poems)

    print("\n已生成：")
    print(f"- {OUT_LONG}")
    print(f"- {OUT_WIDE}")
    print(f"- {OUT_SUMMARY}")
    print("- unmatched_yearly_poems.json")


if __name__ == "__main__":
    main()