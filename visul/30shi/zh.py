import json
import opencc

def translate_to_simplified(data, converter):
    """
    递归遍历数据结构，将其中的所有字符串从繁体转换为简体。
    支持嵌套的字典(dict)和列表(list)。
    """
    if isinstance(data, dict):
        # 如果是字典，递归处理它的每一个值 (键名通常不需要转换，如果需要，也可以对 k 进行转换)
        return {k: translate_to_simplified(v, converter) for k, v in data.items()}
    elif isinstance(data, list):
        # 如果是列表，递归处理里面的每一个元素
        return [translate_to_simplified(item, converter) for item in data]
    elif isinstance(data, str):
        # 如果是字符串，直接执行转换
        return converter.convert(data)
    else:
        # 如果是数字、布尔值或 None，保持原样返回
        return data

def process_poem_file(input_filepath, output_filepath):
    # 初始化 OpenCC 转换器
    # 't2s.json' 代表 Traditional to Simplified (繁体转简体)
    converter = opencc.OpenCC('t2s')

    print("正在读取文件并进行繁简转换...")
    
    try:
        # 1. 读取原有的繁体 JSON 文件 (注意明确使用 utf-8 编码)
        with open(input_filepath, 'r', encoding='utf-8') as file:
            traditional_data = json.load(file)

        # 2. 执行转换
        simplified_data = translate_to_simplified(traditional_data, converter)

        # 3. 将转换后的数据保存为新的 JSON 文件
        with open(output_filepath, 'w', encoding='utf-8') as file:
            # ensure_ascii=False 确保中文字符正常保存，而不是变成 \uXXXX 格式
            # indent=4 保持输出文件的美观排版
            json.dump(simplified_data, file, ensure_ascii=False, indent=4)

        print(f"✅ 转换成功！文件已保存至: {output_filepath}")

    except FileNotFoundError:
        print(f"❌ 错误: 找不到文件 '{input_filepath}'，请检查文件路径和名称是否正确。")
    except json.JSONDecodeError:
        print(f"❌ 错误: 文件 '{input_filepath}' 不是一个有效的 JSON 格式。")
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")

# ==========================================
# 在这里配置你的文件名
# ==========================================
# 假设你的原文件名为 traditional_poems.json
INPUT_FILE = r'30shi\result.json' 

# 转换后保存的新文件名
OUTPUT_FILE = r'30shi\rsimplified_poems.json' 

if __name__ == '__main__':
    process_poem_file(INPUT_FILE, OUTPUT_FILE)