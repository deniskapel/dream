import logging
import os
import pickle
import random
import time

from flask import Flask, request, jsonify
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from deeppavlov import build_model

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'), integrations=[FlaskIntegration()])

FILTER_FREQ = False

config_name = os.getenv("CONFIG")

with open("google-10000-english-no-swears.txt", 'r') as fl:
    lines = fl.readlines()
    freq_words = [line.strip() for line in lines]
    freq_words = set(freq_words[:800])

with open("sentences.pickle", 'rb') as fl:
    test_sentences = pickle.load(fl)

try:
    fact_retrieval = build_model(config_name, download=True)
    for i in range(50):
        utt = random.choice(test_sentences)
        test_res = fact_retrieval([utt], [utt], [["moscow"]], [[["Moscow"]]])
    logger.info("model loaded, test query processed")
except Exception as e:
    sentry_sdk.capture_exception(e)
    logger.exception(e)
    raise e

app = Flask(__name__)


def check_utterance(question, bot_sentence):
    question = question.lower()
    bot_sentence = bot_sentence.lower()
    check = False
    lets_talk_phrases = ["let's talk about", "let us talk about", "let's discuss", "let us discuss",
                         "what do you think about", "what's your opinion about", "do you know"]
    for phrase in lets_talk_phrases:
        if phrase in question:
            return True
    greeting_phrases = ["what do you wanna talk about",
                        "what do you want to talk about",
                        "what would you like to chat about",
                        "what are we gonna talk about",
                        "what are your hobbies",
                        "what are your interests"]
    for phrase in greeting_phrases:
        if phrase in bot_sentence:
            return True
    return check


@app.route("/model", methods=['POST'])
def respond():
    st_time = time.time()
    cur_utt = request.json.get("human_sentences", [" "])
    dialog_history = request.json.get("dialog_history", [" "])
    cur_utt = [utt.lstrip("alexa") for utt in cur_utt]
    nounphr_list = request.json.get("entity_substr", [])
    if FILTER_FREQ:
        nounphr_list = [[nounphrase for nounphrase in nounphrases if nounphrase not in freq_words]
                        for nounphrases in nounphr_list]
    if not nounphr_list:
        nounphr_list = [[] for _ in cur_utt]
    entity_pages = request.json.get("entity_pages", [])
    if not entity_pages:
        entity_pages = [[] for _ in cur_utt]

    nf_numbers, f_utt, f_dh, f_nounphr_list, f_entity_pages = [], [], [], [], []
    for n, (utt, dh, nounphrases, input_pages) in \
            enumerate(zip(cur_utt, dialog_history, nounphr_list, entity_pages)):
        if utt not in freq_words and nounphrases:
            f_utt.append(utt)
            f_dh.append(dh)
            f_nounphr_list.append(nounphrases)
            f_entity_pages.append(input_pages)
        else:
            nf_numbers.append(n)

    out_res = [[] for _ in cur_utt]
    try:
        if f_utt:
            fact_res = fact_retrieval(f_utt, f_dh, f_nounphr_list, f_entity_pages)
            out_res = []
            cnt_fnd = 0
            for i in range(len(cur_utt)):
                if i in nf_numbers:
                    out_res.append([])
                else:
                    if cnt_fnd < len(fact_res):
                        out_res.append(fact_res[cnt_fnd])
                        cnt_fnd += 1
                    else:
                        out_res.append([])
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.exception(e)
    total_time = time.time() - st_time
    logger.info(f'fact_retrieval exec time: {total_time:.3f}s')
    return jsonify(out_res)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=3000)