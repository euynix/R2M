import os
import pandas as pd
import numpy as np
from scipy.stats import percentileofscore
from gensim import corpora, models
from nltk.tokenize import WhitespaceTokenizer
# from A_convert_pdf_to_text import clean_up
# from B_preprocess_and_glue_text import preprocess_text, glue_text
import time

data_path = os.path.dirname(__file__)

def load_corpus_dictionary(file_name_startwith):
    corpus = corpora.MmCorpus(file_name_startwith + '.mm')
    dictionary = corpora.Dictionary.load(file_name_startwith + '.dict')
    # print('Corpus length:{}'.format(len(corpus)))
    # print('Dictionary length:{}'.format(len(dictionary)))
    return corpus, dictionary


def create_keyword_dict(dt_keyword, dt_score, dictionary):
    keyword_score = dt_keyword.merge(dt_score, 'left', left_on='glue_word', right_on='dictionary_keyword')
    keyword_score = keyword_score[["glue_word", "score"]]
    keyword_score = keyword_score.rename(columns={"glue_word": "keyword"})
    keyword_score.fillna(1, inplace=True)
    keyword_score.drop_duplicates(inplace=True)
    keyword_list = keyword_score.keyword.tolist()
    keyword_list = [one_key.strip() for one_key in keyword_list]
    keyword_id = []
    for one_key in keyword_list:
        if one_key in dictionary.values():
            keyword_id.append(dictionary.token2id[one_key])
        else:
            keyword_id.append(-999)
    score = keyword_score.score.tolist()
    keyword_list = [one_key for one_key, one_keep in zip(keyword_list, keyword_id) if one_keep != -999]
    score = [one_score for one_score, one_keep in zip(score, keyword_id) if one_keep != -999]
    keyword_id = [one_id for one_id in keyword_id if one_id != -999]
    return keyword_list, keyword_id, score


def prep_relevance(lda, fnames_argsort):
    topic = lda.state.get_lambda()
    topic = topic / topic.sum(axis=1)[:, None]
    topic_term_dists = topic[:, fnames_argsort]
    ## compute relevance and top terms for each topic
    # lift = np.log(topic_term_dists / term_proportion)
    # lift = topic_term_dists / term_proportion
    lift = topic_term_dists / topic_term_dists.sum(0)
    # ttd = np.log(topic_term_dists)
    ttd = topic_term_dists
    return lift, ttd


# def prep_prop_relevance(lda):
#     topic = lda.state.get_lambda()
#     topic = topic / topic.sum(axis=1)[:, None]
#     topic_term_dists = topic[:, fnames_argsort]
#     ## compute relevance and top terms for each topic
#     # lift = np.log(topic_term_dists / term_proportion)
#     lift = topic_term_dists / term_proportion
#     # lift = lift/lift.sum(1)[:,None]
#     # ttd = np.log(topic_term_dists)
#     ttd = topic_term_dists
#     return lift, ttd


def cal_relevance(lift, ttd, lambda_):
    relevance = lambda_ * ttd + (1 - lambda_) * lift  # weighted word-topic matrix
    # relevance=relevance/relevance.sum(axis=1)[:, None]
    return relevance


# def rel_relevance(lift, ttd, lambda_):
#     relevance = lambda_ * ttd + (1 - lambda_) * lift  # weighted word-topic matrix
#     relevance = relevance / relevance.sum(axis=1)[:, None]
#     return relevance


def generate_marketness(word_topic_mat, keyword_id, score_list):
    #    keyword_removed=[one for one in keyword_list if one not in keyword_dico]
    #    print  keyword_removed
    word_topic_mat_keyword = word_topic_mat[:, keyword_id]
    word_topic_mat_keyword_score = np.array(word_topic_mat_keyword) * np.array(score_list)
    topic_mktness = list(word_topic_mat_keyword_score.sum(axis=1))
    return topic_mktness


def generate_aR2M(doc_topic_mat, topic_mktness):
    # avg_mktness
    avg_r2m = np.dot(doc_topic_mat, np.array(topic_mktness))
    return avg_r2m


def generate_eR2M(doc_topic_mat, topic_mktness):
    foo = np.multiply(np.log(doc_topic_mat), doc_topic_mat)
    entropy_r2m = np.where(np.isnan(foo), 0, foo).dot(np.array(topic_mktness))
    entropy_r2m = -entropy_r2m
    return entropy_r2m


# def generate_R2M(paper_info, doc_topic_mat, avg_r2m, entropy_r2m, lambda_seq):
#     avg_r2m = pd.DataFrame(avg_r2m)
#     avg_r2m.columns = ["aR2M_" + str(round(one_l, 1)) for one_l in lambda_seq]
#     entropy_r2m = pd.DataFrame(entropy_r2m)
#     entropy_r2m.columns = ["eR2M_" + str(round(one_l, 1)) for one_l in lambda_seq]
#     doc_topic_mat = pd.DataFrame(doc_topic_mat)
#     r2m_mat = pd.concat([paper_info, avg_r2m, entropy_r2m, doc_topic_mat], axis=1)
#
#     pd.DataFrame(r2m_mat).to_csv(file_name_startwith + "_R2M_topics_" + str(num_topics) + ".csv")
#     return r2m_mat


def extract_predictions(text):
    # load whole corpus
    corpus, dictionary = load_corpus_dictionary(data_path + '/glue_trial_')
    fnames_argsort = np.asarray(list(dictionary.token2id.values()), dtype=np.int_)

    # load dictionary and weights
    N = pd.read_excel(data_path + '/Cleaned_AllDictionary2020.xlsx', sheet_name='Sheet1', header=0)
    mkt_score = pd.read_excel(data_path + '/2020_dictionary_score.xlsx', sheet_name="2020_dictionary_score", header=0)
    keyword_list, keyword_id, score = create_keyword_dict(N, mkt_score, dictionary)

    # load LDA model
    num_topics = 40
    num_words = 30

    # topic labels
    topic_labels = ["Market Entry", "Consumer Judgment", "Dynamic Models", "Pricing", "Social Networks",
                    "Measurement Scales", "Online Marketing", "Consumer Goals and Motives",
                    "Home Consumption", "CRM", "Power and Agency", "Experiential Marketing",
                    "Multiattribute models/Conjoint", "Innovations", "Information Processing",
                    "Time and Distance Perception", "Choice Theory", "Measurement", "Advertising", "Marketing Theory",
                    "Behavioral Segmentation", "Product Management",
                    "Household Purchase Behavior", "Family and Socialization", "Affect", "Movies Marketing",
                    "Salesforce Management", "Behavioral Decision Theory",
                    "Branding", "Financial Impact", "Consumer Culture Theory", "Empirical Estimation", "Marketing Strategy",
                    "Self", "Game Theory", "Market Orientation",
                    "Channel Management", "Analytical Models", "Salesforce Compensation", "Sales Promotion"]

    eR2M1_list = pd.read_csv(data_path + "/eR2M1.csv")['eR2M_1.0'].tolist()
    further_stop = pd.read_csv(data_path + '/further_stop.csv').iloc[:, 0].tolist()
    lda = models.LdaModel.load(data_path + "/glue_trial_" + "_LDA_Model" + str(num_topics) + "_20200624_0107", mmap='r')
    lift, ttd = prep_relevance(lda, fnames_argsort)
    # lambda_seq = [0, 1]

    text_tokens = WhitespaceTokenizer().tokenize(text)
    text_tokens = [s for s in text_tokens if s not in further_stop]

    # create prediction corpus
    tpm_corpus = [dictionary.doc2bow(text_tokens)]
    tpm_doc_topic_mat = np.zeros((len(tpm_corpus), num_topics))

    for ind, one_sch in enumerate(tpm_corpus):
        tpm_lda = lda[one_sch]
        for (tp, w) in tpm_lda:
            tpm_doc_topic_mat[ind, tp] = w

    lambda_seq = [1]  #### we might change this later!!!!!

    # raw relevance
    avg_R2M = np.zeros((len(tpm_corpus), len(lambda_seq)))
    entropy_R2M = np.zeros((len(tpm_corpus), len(lambda_seq)))

    for col, lambda_ in enumerate(lambda_seq):
        relevance = cal_relevance(lift, ttd, lambda_)
        topic_mktness = generate_marketness(relevance, keyword_id, score)
        avg_R2M[:, col] = generate_aR2M(tpm_doc_topic_mat, topic_mktness)
        entropy_R2M[:, col] = generate_eR2M(tpm_doc_topic_mat, topic_mktness)

    # Output for Web App
    # 1. paper info
    # file_name = your_file_name_from_web_input  ###  edit this accordingly!!!

    # 2. R2M scores
    # print("The R2M score of the uploaded paper is in ***% quantile")
    entropy_score_quantile = round(percentileofscore(eR2M1_list, entropy_R2M[:, :]), -1)

    # 3. paper topic probability and marketingness
    # topic_marketingness_quantile = [round(percentileofscore(topic_mktness, onenumber), -1) for onenumber in topic_mktness]
    # df_prediction = pd.DataFrame(
    #     {"Top_three_topic": topic_labels, 'Topic_probability': tpm_doc_topic_mat.reshape((num_topics,)),
    #      "Topic_marketingness_in_quantile": topic_marketingness_quantile})
    # df_prediction = df_prediction.sort_values(by=['Topic_probability'], ascending=False)
    #
    # df_prediction_top_three = df_prediction[["Top_three_topic", "Topic_marketingness_in_quantile"]].head(n=3)
    # print("this is the data frame you need", df_prediction_top_three)
    return entropy_score_quantile\
        # , df_prediction_top_three

# if __name__ == "__main__":
#     path = "/Users/xinyueli/Desktop/R2M/papers/JM2020EBSCO_unseen.pdf"
#     t1 = time.time()
#     cleaned_text = clean_up(path)
#     t2 = time.time()
#     print(t2-t1)
#     preprocessed_text = preprocess_text(cleaned_text)
#     t3 = time.time()
#     print(t3-t2)
#     glued_text = glue_text(preprocessed_text)
#     t4 = time.time()
#     print(t4-t3)
#     res = extract_predictions(glued_text)
#     t5 = time.time()
#     print(t5-t4)
#     print(res)
#






