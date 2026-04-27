import json
import re


POEMS_PATH = "sampled_1000_imagery_poems.json"
TIME_PATH = "time.txt"
OUTPUT_PATH = "poem_time_visual.json"


# ============================================================
# 1. 作者生卒年表
# 你可以继续补充自己的30位诗人
# ============================================================

AUTHOR_LIFE = {
   "杨炯": (650, 693),
    "卢照邻": (637, 689),
    "骆宾王": (619, 687),
    "陈子昂": (661, 702),
    "张若虚": (660, 720),
    "贺知章": (659, 744),
    "王之涣": (688, 742),
    "孟浩然": (689, 740),
    "王昌龄": (698, 757),
    "王维": (701, 761),
    "李白": (701, 762),
    "高适": (704, 765),
    "岑参": (715, 770),
    "杜甫": (712, 770),
    "韦应物": (737, 792),
    "孟郊": (751, 814),
    "韩愈": (768, 824),
    "柳宗元": (773, 819),
    "刘禹锡": (772, 842),
    "白居易": (772, 846),
    "元稹": (779, 831),
    "李贺": (790, 816),
    "贾岛": (779, 843),
    "杜牧": (803, 852),
    "杜荀鹤": (846, 904),
    "皮日休": (834, 883),
    "温庭筠": (812, 866),
    "李商隐": (813, 858),
    "罗隐": (833, 909),
    "王勃": (650, 676),
}


# ============================================================
# 2. 基础工具函数
# ============================================================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_text(s):
    """
    用于标题匹配：
    去掉空格、书名号、常见标点，降低匹配失败概率。
    """
    if s is None:
        return ""

    s = str(s).strip()
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[《》〈〉「」『』“”\"'，,。.!！?？；;：:、（）()【】\[\]]", "", s)
    return s


def clean_author(author):
    if not author:
        return ""
    return str(author).strip()


def clean_title(title):
    if not title:
        return ""
    return str(title).strip()


# ============================================================
# 3. 解析 time.txt
# ============================================================

def parse_year_info(time_text):
    """
    从 time.txt 的时间字段里解析年份。

    可识别：
    约 750s
    约 748-749
    840s
    850s-860s
    724
    730s
    """
    if not time_text:
        return None, [None, None], "low"

    text = str(time_text)

    # 先找 850s-860s 这种
    m = re.search(r"(\d{3,4})s\s*[-—~～]\s*(\d{3,4})s", text)
    if m:
        start = int(m.group(1))
        end = int(m.group(2)) + 9
        estimated = (start + end) // 2
        return estimated, [start, end], "medium"

    # 找 748-749 / 810-820 这种
    m = re.search(r"(\d{3,4})\s*[-—~～]\s*(\d{3,4})", text)
    if m:
        start = int(m.group(1))
        end = int(m.group(2))
        estimated = (start + end) // 2

        # 区间很短，置信度较高
        if end - start <= 3:
            confidence = "high"
        else:
            confidence = "medium"

        return estimated, [start, end], confidence

    # 找 750s / 820s 这种
    m = re.search(r"(\d{3,4})s", text)
    if m:
        start = int(m.group(1))
        end = start + 9
        estimated = start + 5
        return estimated, [start, end], "medium"

    # 找单一年份 724 / 759 这种
    m = re.search(r"(\d{3,4})", text)
    if m:
        year = int(m.group(1))
        return year, [year, year], "high"

    return None, [None, None], "low"


def parse_time_line(line):
    """
    解析 time.txt 中的一行。

    支持格式：
    诗名,作者,创作时间（备注）
    诗名，作者，创作时间（备注）

    返回：
    {
      title,
      author,
      raw_time,
      estimated_year,
      year_range,
      confidence,
      note
    }
    """
    line = line.strip()

    if not line:
        return None

    if line.startswith("诗名") or line.startswith("title"):
        return None

    # 兼容英文逗号和中文逗号
    line = line.replace("，", ",")

    parts = line.split(",", 2)

    if len(parts) < 3:
        print(f"跳过无法解析的行：{line}")
        return None

    title = clean_title(parts[0])
    author = clean_author(parts[1])
    raw_time = parts[2].strip()

    estimated_year, year_range, confidence = parse_year_info(raw_time)

    return {
        "title": title,
        "author": author,
        "raw_time": raw_time,
        "estimated_year": estimated_year,
        "year_range": year_range,
        "confidence": confidence,
        "note": raw_time
    }


def load_time_file(path):
    """
    读取 time.txt，并建立两个索引：
    1. title + author 精确匹配
    2. title 单独匹配兜底
    """
    time_by_title_author = {}
    time_by_title = {}

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            item = parse_time_line(line)

            if item is None:
                continue

            title_key = normalize_text(item["title"])
            author_key = normalize_text(item["author"])
            title_author_key = (title_key, author_key)

            time_by_title_author[title_author_key] = item

            # 标题兜底索引：如果重名，保留第一个
            if title_key not in time_by_title:
                time_by_title[title_key] = item

    return time_by_title_author, time_by_title


# ============================================================
# 4. 判断唐代时期、人生阶段
# ============================================================

def get_tang_period(year):
    """
    唐诗内部时间分期。
    这里采用常见文学史粗分：
    初唐：618-712
    盛唐：713-765
    中唐：766-835
    晚唐：836-907
    """
    if year is None:
        return "未知"

    if 618 <= year <= 712:
        return "初唐"
    elif 713 <= year <= 765:
        return "盛唐"
    elif 766 <= year <= 835:
        return "中唐"
    elif 836 <= year <= 907:
        return "晚唐"
    else:
        return "未知"


def get_life_stage(author, year):
    """
    根据作者生年和估计年份判断人生阶段。
    """
    if year is None:
        return "未知"

    life = AUTHOR_LIFE.get(author)

    if life is None:
        return "未知"

    birth, death = life
    age = year - birth

    if age < 0:
        return "未知"

    if age <= 30:
        return "早年"
    elif age <= 50:
        return "中年"
    else:
        return "晚年"


def get_author_birth_death(author):
    life = AUTHOR_LIFE.get(author)

    if life is None:
        return None, None

    return life[0], life[1]


# ============================================================
# 5. 合并 sampled_1000_imagery_poems.json 和 time.txt
# ============================================================

def find_time_info(poem, time_by_title_author, time_by_title):
    title = poem.get("title", "")
    author = poem.get("author", "")

    title_key = normalize_text(title)
    author_key = normalize_text(author)

    # 优先 title + author 匹配
    item = time_by_title_author.get((title_key, author_key))

    if item:
        return item

    # 其次只用标题匹配
    item = time_by_title.get(title_key)

    if item:
        return item

    return None


def build_poem_time_json(poems, time_by_title_author, time_by_title):
    result = []
    unmatched = []

    for index, poem in enumerate(poems, start=1):
        title = clean_title(poem.get("title", ""))
        author = clean_author(poem.get("author", ""))

        time_info = find_time_info(poem, time_by_title_author, time_by_title)

        author_birth, author_death = get_author_birth_death(author)

        if time_info:
            estimated_year = time_info["estimated_year"]
            year_range = time_info["year_range"]
            confidence = time_info["confidence"]
            raw_time = time_info["raw_time"]
            time_source = f"人工标注/{raw_time}"
        else:
            estimated_year = None
            year_range = [None, None]
            confidence = "low"
            raw_time = ""
            time_source = "未在 time.txt 中匹配到"

            unmatched.append({
                "title": title,
                "author": author,
                "id": poem.get("id")
            })

        life_stage = get_life_stage(author, estimated_year)
        tang_period = get_tang_period(estimated_year)

        item = {
            "id": poem.get("id", f"poem_{index:03d}"),
            "title": title,
            "author": author,

            "author_birth": author_birth,
            "author_death": author_death,

            "estimated_year": estimated_year,
            "year_range": year_range,

            "life_stage": life_stage,
            "tang_period": tang_period,

            "confidence": confidence,
            "time_source": time_source,

            "matched_imagery": poem.get("matched_imagery", [])
        }

        result.append(item)

    return result, unmatched


# ============================================================
# 6. 主程序
# ============================================================

def main():
    poems = load_json(POEMS_PATH)

    time_by_title_author, time_by_title = load_time_file(TIME_PATH)

    result, unmatched = build_poem_time_json(
        poems,
        time_by_title_author,
        time_by_title
    )

    save_json(result, OUTPUT_PATH)

    print("=" * 50)
    print(f"诗歌总数：{len(poems)}")
    print(f"time.txt 中时间记录数：{len(time_by_title_author)}")
    print(f"成功输出：{len(result)}")
    print(f"未匹配时间：{len(unmatched)}")
    print(f"已保存到：{OUTPUT_PATH}")

    if unmatched:
        print("\n未匹配到时间的前20首：")
        for item in unmatched[:20]:
            print(f"{item['author']}《{item['title']}》")

        with open("unmatched_time_poems.json", "w", encoding="utf-8") as f:
            json.dump(unmatched, f, ensure_ascii=False, indent=2)

        print("\n未匹配列表已保存到：unmatched_time_poems.json")


if __name__ == "__main__":
    main()