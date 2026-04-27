import json
import csv

INPUT_PATH = "sampled_1000_imagery_poems.json"
OUTPUT_PATH = "poem_titles_with_author.csv"

with open(INPUT_PATH, "r", encoding="utf-8") as f:
    poems = json.load(f)

with open(OUTPUT_PATH, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["title", "author", "id"])

    for poem in poems:
        writer.writerow([
            poem.get("title", "").strip(),
            poem.get("author", "").strip(),
           
        ])

print(f"提取完成，共 {len(poems)} 首")
print(f"已保存到：{OUTPUT_PATH}")