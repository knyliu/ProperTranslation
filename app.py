from flask import Flask, request, render_template
import jieba
import io
import os
import re
import requests, uuid, json
from azure.ai.textanalytics import TextAnalyticsClient, ExtractiveSummaryAction
from azure.core.credentials import AzureKeyCredential

app = Flask(__name__)

folder_path = 'data_all_json'

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
    summary_result = None
    key_phrases_info = None
    key_phrases_info_list = ["","","","",""]
    sentence = ''
    numbers = []

    if request.method == 'POST':
        sentence = request.form.get('sentence', '')
        numbers = request.form.getlist('numbers')

        print("Selected options:", numbers)

        user_input = ','.join(numbers)
        documents = [sentence]
        summary_result = extract_summary(sentence)
        result = translate_zh_en(documents, user_input, folder_path)

        ES_API_KEY = os.getenv('ES_API_KEY')
        endpoint = "https://language-service-20231031-1.cognitiveservices.azure.com/"
        key_phrases_info = extract_top_key_phrases(sentence, endpoint, ES_API_KEY, top_n=5)
        key_phrases_info_list = key_phrases_info.split(',')

    return render_template('translate_zh_en.html', result=result, summary_result = summary_result, key_phrases_info = key_phrases_info_list[0], key_phrases_info_1 = key_phrases_info_list[1], key_phrases_info_2 = key_phrases_info_list[2], key_phrases_info_3 = key_phrases_info_list[3], key_phrases_info_4 = key_phrases_info_list[4], sentence=sentence, numbers=','.join(numbers))

# 英翻中路由
@app.route('/translate-en-zh', methods=['GET', 'POST'])
def translate_en_zh_route():
    result = None
    summary_result = None
    key_phrases_info = None
    key_phrases_info_list = ["","","","",""]
    sentence = ''
    numbers = []

    if request.method == 'POST':
        sentence = request.form.get('sentence', '')
        numbers = request.form.getlist('numbers')

        print("Selected options:", numbers)

        user_input = ','.join(numbers)
        documents = [sentence]
        result = translate_en_zh(documents, user_input, folder_path)
        summary_result = extract_summary(result)


        ES_API_KEY = os.getenv('ES_API_KEY')
        endpoint = "https://language-service-20231031-1.cognitiveservices.azure.com/"
        key_phrases_info = extract_top_key_phrases(sentence, endpoint, ES_API_KEY, top_n=5)
        key_phrases_info_list = key_phrases_info.split(',')


    return render_template('translate_en_zh.html', result=result, summary_result = summary_result, key_phrases_info = key_phrases_info_list[0], key_phrases_info_1 = key_phrases_info_list[1], key_phrases_info_2 = key_phrases_info_list[2], key_phrases_info_3 = key_phrases_info_list[3], key_phrases_info_4 = key_phrases_info_list[4], sentence=sentence, numbers=','.join(numbers))



# 中翻英的功能實現
def translate_zh_en(documents, user_input, folder_path):
    # Split user input into file names
    file_names = [name.strip() for name in user_input.split(',')]

    # Create a dictionary to store the contents of all files
    all_lists = {}

    # Read the specified files from the 'data_all_json' folder
    for file_name in file_names:
        file_path = os.path.join(folder_path, file_name + '.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                # Store the file's dictionaries in all_lists with the file name as key
                all_lists[file_name] = json.load(file)
        else:
            print(f"File '{file_name}' does not exist.")

    user_input = user_input

    selected_keys = [key.strip() for key in user_input.split(',')]

    merged_list = []

    for key in selected_keys:
        if key in all_lists:
            print(f"Key '{key}'")
            # print(f"Key '{key}': {all_lists[key]}")
            merged_list.extend(all_lists[key]) 
        else:
            print(f"The key name '{key}' does not exist.")


    print(merged_list)


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
    key = os.getenv('API_KEY')
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
def translate_en_zh(documents, user_input, folder_path):
    # Split user input into file names
    file_names = [name.strip() for name in user_input.split(',')]

    # Create a dictionary to store the contents of all files
    all_lists = {}

    # Read the specified files from the 'data_all_json' folder
    for file_name in file_names:
        file_path = os.path.join(folder_path, file_name + '.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                # Store the file's dictionaries in all_lists with the file name as key
                all_lists[file_name] = json.load(file)
        else:
            print(f"File '{file_name}' does not exist.")

    # Merge the dictionaries from all files into a single list
    ch_eng = [entry for sublist in all_lists.values() for entry in sublist]

    # Create a mapping of lower case English terms to their Chinese equivalents
    lowercase_mapping = {value.lower(): key for sublist in all_lists.values() for entry in sublist for key, value in entry.items()}

    # Create a function to replace matched words
    def replace_match(match):
        word = match.group(0)
        # Check for lowercase word in the mapping
        return lowercase_mapping.get(word.lower(), word)

    # Use a regular expression to replace words in the document
    pattern = r'\b' + r'\b|\b'.join(re.escape(word) for word in lowercase_mapping) + r'\b'
    documents[0] = re.sub(pattern, replace_match, documents[0], flags=re.IGNORECASE)

    print(documents[0])
    sentence = documents[0]

    # Add your key and endpoint
    key = os.getenv('API_KEY')
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



# 文字摘要
def extract_summary(documents):
    key = os.getenv('ES_API_KEY')
    endpoint = "https://language-service-20231031-1.cognitiveservices.azure.com/"

    try:
        ta_credential = AzureKeyCredential(key)
        text_analytics_client = TextAnalyticsClient(
            endpoint=endpoint, 
            credential=ta_credential)

        document = [documents]
        poller = text_analytics_client.begin_analyze_actions(
            document,
            actions=[ExtractiveSummaryAction(max_sentence_count=4)],
        )

        document_results = poller.result()
        print(document_results)
        for result in document_results:
            extract_summary_result = result[0]
            if extract_summary_result.is_error:
                return "錯誤: '{}' - '{}'".format(
                    extract_summary_result.code, extract_summary_result.message
                )
            else:
                return " ".join([sentence.text for sentence in extract_summary_result.sentences])
    except Exception as e:
        return str(e)
    
# 主詞分析
def extract_top_key_phrases(documents, endpoint, key, top_n=5):
    # Setup for key phrases extraction
    credential = AzureKeyCredential(key)
    text_analytics_client = TextAnalyticsClient(endpoint=endpoint, credential=credential)

    documents = [documents]

    try:
        # Key phrases extraction
        key_phrases_response = text_analytics_client.extract_key_phrases(documents, language="zh-Hant")
        key_phrases_docs = [doc for doc in key_phrases_response if not doc.is_error]

        # Select top N key phrases
        key_phrases_info = ""
        if key_phrases_docs and key_phrases_docs[0].key_phrases:
            top_key_phrases = key_phrases_docs[0].key_phrases[:top_n]  # Get top N key phrases
            key_phrases_info = ", ".join(top_key_phrases)
        else:
            key_phrases_info = "主詞：無"

    except Exception as e:
        key_phrases_info = "提取主詞過程中發生錯誤: " + str(e)

    return key_phrases_info



if __name__ == '__main__':
    app.run(debug=True)
