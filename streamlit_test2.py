import streamlit as st
import numpy as np
# from streamlit_webrtc import VideoTransformerBase, VideoTransformerContext
import openai, os, time
import whisper
model = whisper.load_model("base")


def on_input_change():
    user_input = st.session_state.user_input
    st.session_state.past_busniess.append(user_input)
    # st.session_state.generated_busniess.append("The messages from Bot\nWith new line")

def on_btn_click():
    del st.session_state.past[:]
    del st.session_state.generated[:]

os.environ["OPENAI_API_KEY"] = 'sk-Hzurbmv9pkXmeVt3255b7a5e73674452BdEa0c2630Bd2f1a'
openai.api_base = "https://one-api.myscale.cloud/v1"
openai.api_key = os.environ["OPENAI_API_KEY"]


def get_embedding(query, model="text-embedding-ada-002"):
        text = query.replace("\n", " ")
        return openai.Embedding.create(input = [text], model=model)['data'][0]['embedding']


def get_completion_from_messages(messages, 
                                 model="gpt-3.5-turbo-16k", 
                                 temperature=0, max_tokens=1000):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, 
        max_tokens=max_tokens, 
    )
    return response.choices[0].message["content"]


#Creating the chatbot interface
st.title("AiTA")

#logo = Image.open('https://www.groundzeroweb.com/wp-content/uploads/2017/05/Funny-Cat-Memes-11.jpg')
st.sidebar.image("https://www.groundzeroweb.com/wp-content/uploads/2017/05/Funny-Cat-Memes-11.jpg", width=210)

with st.sidebar.expander("About the App"):
    st.write("""
        使用LLM + Whisper的能力对雅思口语进行打分
    """)

def get_text():
    input_text = st.text_input("You: ","你好，请做个自我介绍", key="input")
    return input_text

def get_text_2():
    input_text = st.text_input("You: ","你好，给我讲一个英文的绕口令吧", key="input")
    return input_text

# Storing the chat

if 'past' not in st.session_state:
    st.session_state['past'] = []

if 'generated' not in st.session_state:
    st.session_state['generated'] = []


    
col3, col4 = st.columns(2)
with col3:
    uploaded_file = st.file_uploader("请选择一个 mp3 或 m4a 文件", type=['mp3', 'm4a'])
    
    if uploaded_file is not None:
        file_details = {"FileName":uploaded_file.name, "FileType":uploaded_file.type, "FileSize":uploaded_file.size}
        filepath = os.path.join('/home/ubuntu/xuying/', uploaded_file.name)
        
        with open(filepath, 'wb') as f:
            f.write(uploaded_file.getvalue())
            
        if st.button('Start grading'):
            with st.spinner("waiting for grading"):
                result = model.transcribe(filepath)
                system_message = '''你是一个雅思英语老师和markdown 高手，请给下面这篇口语打分并且用中文说明原因，
                根据雅思的口语评判标准，给出打分的原因。打分的标准是：雅思考试口语评分标准主要包括四个方面，分别是流利性与连贯性、词汇多样性、语法多样性及准确性、以及发音。每个方面都有具体的表现和要求，共有9个分数等级，从9分到0分。
                以下是每个分数等级的要求：

                Band Score 9：流利地表达，几乎没有重复或自我纠正，犹豫只是基于思考内容而非寻找词汇或语法。连贯表达，使用丰富多样的连接词。词汇资源广泛，运用准确。使用习语自然准确。语法多样性广泛，准确性高。发音准确且自然，易于理解。

                Band Score 8：流利表达，偶尔有重复或自我纠正，犹豫主要基于思考内容。连贯表达，使用较广泛的连接词。词汇资源丰富且使用灵活，但可能有少量不准确。使用非常见词汇和习语较为熟练，但可能偶尔有不准确。语法结构灵活且大部分准确，只有极个别错误。发音使用多种特点，准确度高，但偶尔有偏差。

                Band Score 7：表达详尽，虽然有时会有犹豫或重复，但没有明显困难。使用一定灵活的连接词和语篇标记。词汇丰富，能讨论各种话题，但可能会出现不准确。使用少量非常见词汇和习语，但有时不准确。能进行有效的改述。语法结构灵活，虽然有时会有错误，但不影响理解。发音使用多种特点，但可能掌握程度不一。

                Band Score 6：表现出充分交流的意愿，但偶尔有重复、自我纠正或犹豫。使用一系列连接词和语篇标记，但连贯性不稳定。词汇量充足，能谈论各种话题，但有时使用不当。能进行基本改述。使用简单和复杂句型，但灵活性有限，有时会出现错误。发音使用多种特点，但掌握程度不一，有时偏差频繁。

                Band Score 5：通常能保持语流，但可能需要重复、自我纠正或降低语速。连接词使用过度。使用简单的语言流利地表达，但在复杂交流时可能有困难。词汇使用有限，对不熟悉话题只能进行基本表达。尝试进行改述，但成功有限。使用基本句型，但准确度有限，有时依赖预先背诵。发音尝试多种特点，但频繁偏差。

                Band Score 4：作答有明显停顿，语速较慢，频繁重复和自我纠正。连接简单句子，但使用简单的连接词，连贯性较差。能谈论熟悉话题，但对不熟悉话题表达不畅，词汇选择有限。基本上能使用基本句型，但通常出现错误，造成理解困难。发音使用有限的特点，频繁出现偏差。

                Band Score 3：表达过程中出现长时间停顿，连贯性很差。连接简单句子的能力有限。仅能简单作答，常无法表达基本意思。使用简单词汇表达个人信息，对不熟悉话题词汇匮乏。尝试使用基本句型，但准确度有限，常依赖预先背诵。发音尝试多种特点，但频繁偏差。

                Band Score 2：大部分词汇间出现长时间停顿。几乎无法进行沟通，只能说出零散的单词或预先背诵的几句话。不能使用基本的句型。表达通常无法理解。

                Band Score 1：无法进行沟通，只有零散单词或无法评分的语言。

                Band Score 0：缺考。

                这些标准主要考察考生在口语表达方面的能力，包括流利度、词汇运用、语法结构、发音准确等。考生根据自己的口语表达水平，在这些方面不断提高，争取获得更高的分数。
                用英文给出修改建议。并把修改好的原文回答给学生，用中文给出口语批改分数和原因，用英文给出修改建议。
                把回答都整理成markdown格式。
                输出格式；
                ❤ 评分标准及分数 ❤:
                Fluency and coherence  (FC) Band Score:...
                •......
                •......

                Lexical resource (LR) Band Score:...
                •......
                •......

                Grammatical range and accuracy (GRA) Band Score:...
                •......
                •......

                Pronunciation  Band Score:...
                •......
                •......

                Band Score: 分数

                ❤ 原因 ❤ ：
                ❤ 修改建议 ❤ ：
                ❤ 建议更改的词汇解释 ❤ ：
                ❤ 建议更改的句子 ❤  ：
                ❤ 修改之后的口语文章 ❤ ：'''
                user_message = f"""{result}"""
                messages =  [  
                    {'role':'system', 
                    'content': system_message},    
                    {'role':'user', 
                    'content': f"{user_message}"},  
                ] 
                response = get_completion_from_messages(messages)
                with col4:
                    text2 = st.empty()

                    text2.text_area("修改建议", value= response, height=600)


                
            

        
