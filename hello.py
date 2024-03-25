from flask import Flask, request
import json
import pinyin_jyutping

app = Flask(__name__)


@app.route("/", methods=['PUT'])
def hello_world():
    data = request.json['rawString']
    if request.json['exerciseTypeId'] == 0:
        return get_xuan(data)
    return get_duan(data)


def get_duan(raw_passage):
    raw_paragraphs = raw_passage.replace(' ', '').split('\n')

    question_index = 0
    question_flag = False

    curr_option = 1
    options = []

    num_questions = 0

    p = pinyin_jyutping.PinyinJyutping()
    passage = []
    for raw_paragraph in raw_paragraphs:
        all_solutions = p.pinyin_all_solutions(raw_paragraph)
        # Assume every line starts with a tab.
        paragraph_list = [{'characters': '\u2003'}]
        for (hanzi, solutions) in zip(all_solutions['word_list'], all_solutions['solutions']):
            if hanzi == '（' or hanzi == '(':
                question = {'questionIndex': question_index, 'options': []}
                question_flag = True
                num_questions += 1
                continue

            if hanzi == '）' or hanzi == ')':
                question['options'].append(options)
                options = []
                curr_option = 1

                question_index += 1
                question_flag = False
                paragraph_list.append(question)
                continue

            if hanzi in ['c1', 'c2', 'c3', 'c4']:
                correct_index = int(hanzi[1]) - 1
                question['correctIndex'] = correct_index

            solution0 = solutions[0]

            if hanzi in ['2', '3', '4', 'c2', 'c3', 'c4']:
                if hanzi != curr_option:    # Finished processing the option.
                    question['options'].append(options)
                    options = []
                    curr_option += 1
                continue
            if hanzi in ['c1', '1']:
                continue

            # BUG. Need to handle the case with multiple characters.
            if hanzi == solution0:
                word = {'characters': hanzi}
            else:
                word = {'characters': hanzi, 'pinyin': solutions[0]}

            if question_flag:
                options.append(word)
            else:
                paragraph_list.append(word)

        passage.append(paragraph_list)

    output = {'numQuestions': int(num_questions), 'passage': passage}
    return json.dumps(output, ensure_ascii=False, indent=2)


def get_xuan(raw_passage):
    raw_paragraphs = raw_passage.replace(' ', '').split('\n')

    print('raw', raw_paragraphs)

    p = pinyin_jyutping.PinyinJyutping()
    choices = []
    it = iter(raw_paragraphs)
    while (raw_paragraph := next(it)) and raw_paragraph != '\n':
        all_solutions = p.pinyin_all_solutions(raw_paragraph)
        choice = {"words": []}
        for (hanzi, solutions) in zip(all_solutions['word_list'], all_solutions['solutions']):
            choice['words'].append({'hanzi': hanzi, 'pinyin': solutions[0]})
        choices.append(choice)

    passage = []
    question_index = 0
    while (raw_paragraph := next(it, None)) is not None:
        all_solutions = p.pinyin_all_solutions(raw_paragraph)
        # Assume every line starts with a tab.
        paragraph_list = [{'characters': '\u2003'}]
        for (hanzi, solutions) in zip(all_solutions['word_list'], all_solutions['solutions']):
            solution0 = solutions[0]
            if hanzi[0] == 'a':
                word = {'questionIndex': question_index,
                        'correctIndex': int(hanzi[1:])}
                question_index += 1
            elif hanzi == solution0 or hanzi.isdigit():
                word = {'characters': hanzi}
            else:
                word = {'characters': hanzi, 'pinyin': solution0}

            paragraph_list.append(word)
        passage.append(paragraph_list)

    output = {'numQuestions': question_index,
              'choices': choices, 'passage': passage}
    return json.dumps(output, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)
