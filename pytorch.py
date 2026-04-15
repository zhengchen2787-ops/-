import json
import glob
import os

# 1. 定義三十位詩人的繁體字名單 (使用 set 以獲得極快的查找速度)
target_poets = {
    "李白", "杜甫", "白居易", "王維", "孟浩然",
    "王勃", "駱賓王", "楊炯", "盧照鄰", "陳子昂",
    "張若虛", "王昌齡", "王之渙", "岑參", "高適",
    "韓愈", "柳宗元", "劉禹錫", "元稹", "韋應物",
    "賀知章", "孟郊", "賈島", "李賀", "李商隱",
    "杜牧", "溫庭筠", "皮日休", "羅隱", "杜荀鶴"
}

# 2. 路徑配置
# 輸入路徑：匹配 D:\shi 下所有以 poet.tang. 開頭的 JSON 文件
input_pattern = r"D:\shi\poet.tang.*.json"
# 輸出路徑：結果將保存在同一文件夾下
output_file = r"D:\30\filtered_30_poets.json"


def run_filter():
    filtered_results = []

    # 獲取所有符合條件的文件列表
    file_list = glob.glob(input_pattern)

    if not file_list:
        print(f"錯誤：在 D:\shi 下未找到任何 poet.tang.*.json 文件。")
        return

    print(f"開始篩選，共發現 {len(file_list)} 個數據文件...")

    # 3. 循環處理每個文件
    for file_path in file_list:
        file_name = os.path.basename(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # 計算當前文件篩選前的數量
                count_before = len(filtered_results)

                # 遍歷詩歌並篩選
                for poem in data:
                    # 檢查作者是否存在於我們的名單中
                    if poem.get('author') in target_poets:
                        filtered_results.append(poem)

                added = len(filtered_results) - count_before
                print(f"已處理: {file_name} | 本次提取: {added} 首")

        except Exception as e:
            print(f"處理文件 {file_name} 時出錯: {e}")

    # 4. 輸出最終結果
    print("-" * 40)
    print(f"正在將所有結果寫入文件...")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            # indent=4 讓 JSON 文件具備縮進格式，方便人類閱讀
            # ensure_ascii=False 確保繁體中文不會變成轉義編碼
            json.dump(filtered_results, f, ensure_ascii=False, indent=4)

        print(f"【任務成功完成】")
        print(f"篩選後的詩歌總數：{len(filtered_results)} 首")
        print(f"結果文件路徑：{output_path}")

    except Exception as e:
        print(f"保存文件失敗: {e}")


if __name__ == "__main__":
    # 如果輸出路徑需要根據變量動態生成，這裡賦值
    output_path = output_file
    run_filter()