from flask import Flask, request, render_template
import jieba
import io
import requests, uuid, json

app = Flask(__name__)

# 主頁路由
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

# 中翻英路由
@app.route('/translate-zh-en', methods=['GET', 'POST'])
def translate_zh_en_route():
    result = None
    sentence = ''
    numbers = []

    if request.method == 'POST':
        sentence = request.form.get('sentence', '')
        numbers = request.form.getlist('numbers')

        print("Selected options:", numbers)

        user_input = ','.join(numbers)
        documents = [sentence]
        result = translate_zh_en(documents, user_input)

    return render_template('translate_zh_en.html', result=result, sentence=sentence, numbers=','.join(numbers))

# 英翻中路由
@app.route('/translate-en-zh', methods=['GET', 'POST'])
def translate_en_zh_route():
    result = None
    sentence = ''
    numbers = []

    if request.method == 'POST':
        sentence = request.form.get('sentence', '')
        numbers = request.form.getlist('numbers')

        print("Selected options:", numbers)

        user_input = ','.join(numbers)
        documents = [sentence]
        result = translate_en_zh(documents, user_input)

    return render_template('translate_en_zh.html', result=result, sentence=sentence, numbers=','.join(numbers))

# 中翻英的功能實現
def translate_zh_en(documents, user_input):
    ###### all_list 是所有樂詞網上面的資料
    # 从名为 'data_all.json' 的文件中读取数据
    with open('data_all.json', 'r', encoding='utf-8') as file:
        all_lists = json.load(file)

    # 提示用户输入
    user_input = user_input

    # 分割用户输入的字符串，获取键名列表
    selected_keys = [key.strip() for key in user_input.split(',')]

    # 新建一个列表来存储合并后的结果
    merged_list = []

    # 检查并打印用户选择的元素，并将它们添加到合并列表中
    for key in selected_keys:
        if key in all_lists:
            print(f"键 '{key}'")
            # print(f"键 '{key}': {all_lists[key]}")
            merged_list.extend(all_lists[key])  # 将选中的元素添加到合并列表中
        else:
            print(f"键名 '{key}' 不存在。")

    # 打印合并后的列表
    # print("合并后的列表：")
    # print(merged_list)


    ###### ch_eng是最後用來判斷的list，也就是之前最後的merged_list
    ch_eng = merged_list
    # ch_eng = [{"含氮雜環": "nitrogen containing heterocyclic"}, {"手術": "surgery"}]
    userdict_entries = "\n".join(["{} 10 n".format(key) for d in ch_eng for key in d])

    userdict_filelike = io.StringIO(userdict_entries)

    jieba.load_userdict(userdict_filelike)

    words_list = []

    for sentence in documents:
        seg_list = jieba.cut(sentence)
        for word in seg_list:
            words_list.append(word)

    # print(words_list)

    for i, word in enumerate(words_list):
        for dictionary in ch_eng:
            if word in dictionary:
                words_list[i] = dictionary[word]

    # print(words_list)

    sentence = ''.join(words_list)
    # print(sentence)

    # Add your key and endpoint
    key = "6efe201e152c4b23807c8edffd214ac1"
    endpoint = "https://api.cognitive.microsofttranslator.com"

    # location, also known as region.
    # required if you're using a multi-service or regional (not global) resource. It can be found in the Azure portal on the Keys and Endpoint page.
    location = "southeastasia"

    path = '/translate'
    constructed_url = endpoint + path

    params = {
        'api-version': '3.0',
        'from': 'zh-Hant',
        'to': 'en'
    }

    headers = {
        'Ocp-Apim-Subscription-Key': key,
        # location required if you're using a multi-service or regional (not global) resource.
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    # You can pass more than one object in body.
    body = [{
        'text': sentence
    }]

    request = requests.post(constructed_url, params=params, headers=headers, json=body)
    response = request.json()

    # print(json.dumps(response, sort_keys=True, ensure_ascii=False, indent=4, separators=(',', ': ')))

    translated_text = response[0]['translations'][0]['text']
    # print(translated_text)



    return translated_text

# 英翻中的功能實現
def translate_en_zh(documents, user_input):
    ###### all_list 是所有樂詞網上面的資料
    # 从名为 'data_all.json' 的文件中读取数据
    with open('data_all.json', 'r', encoding='utf-8') as file:
        all_lists = json.load(file)

    # 提示用户输入
    user_input = user_input

    # 分割用户输入的字符串，获取键名列表
    selected_keys = [key.strip() for key in user_input.split(',')]

    # 新建一个列表来存储合并后的结果
    merged_list = []

    # 检查并打印用户选择的元素，并将它们添加到合并列表中
    for key in selected_keys:
        if key in all_lists:
            print(f"键 '{key}'")
            # print(f"键 '{key}': {all_lists[key]}")
            merged_list.extend(all_lists[key])  # 将选中的元素添加到合并列表中
        else:
            print(f"键名 '{key}' 不存在。")

    # 打印合并后的列表
    # print("合并后的列表：")
    # print(merged_list)


    ###### ch_eng是最後用來判斷的list，也就是之前最後的merged_list
    ch_eng = merged_list
    # ch_eng = [{"含氮雜環": "nitrogen containing heterocyclic"}, {"手術": "surgery"}]
    for entry in merged_list:
        for key, value in entry.items():
            documents[0] = documents[0].replace(value, key)

    print(documents[0])
    sentence = documents[0]

    # Add your key and endpoint
    key = "6efe201e152c4b23807c8edffd214ac1"
    endpoint = "https://api.cognitive.microsofttranslator.com"

    # location, also known as region.
    # required if you're using a multi-service or regional (not global) resource. It can be found in the Azure portal on the Keys and Endpoint page.
    location = "southeastasia"

    path = '/translate'
    constructed_url = endpoint + path

    params = {
        'api-version': '3.0',
        'from': 'en',
        'to': 'zh-Hant'
    }

    headers = {
        'Ocp-Apim-Subscription-Key': key,
        # location required if you're using a multi-service or regional (not global) resource.
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    # You can pass more than one object in body.
    body = [{
        'text': sentence
    }]
    print(body)

    request = requests.post(constructed_url, params=params, headers=headers, json=body)
    response = request.json()

    # print(json.dumps(response, sort_keys=True, ensure_ascii=False, indent=4, separators=(',', ': ')))

    translated_text = response[0]['translations'][0]['text']
    # print(translated_text)



    return translated_text

if __name__ == '__main__':
    app.run(debug=True)
