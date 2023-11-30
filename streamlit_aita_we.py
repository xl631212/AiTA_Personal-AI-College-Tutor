import streamlit as st
import random
import openai
import os
import streamlit as st
import tempfile
import pdfplumber 
from streamlit_chat import message

# Display some information about the system and additional resources

openai.api_key = os.environ["OPENAI_API_KEY"]


def get_completion_from_messages_new(messages):
    response = client.chat.completions.create(
        model='gpt-4-1106-preview',
        messages=messages,
        temperature=0,
        max_tokens=4000,
    )
    return response.choices[0].message.content

def get_completion_from_messages(messages,
                                 model="gpt-4-1106-preview",
                                 temperature=0, max_tokens=3000):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message["content"]

def create_prompt(reading_level,
                  grade_level

    ):
    education_resources = {
    'reading_levels': {
        'elementary': {
            'description': '主要针对英语学习者的学生，使用常见的基础词汇和短语',
            'reading_speed': '100-150个单词/分钟'
        },
        'intermediate': {
            'description': '主要针对英语作为第二语言的学生，使用更多的词汇和表达方式',
            'reading_speed': '150-200个单词/分钟'
        },
        'advanced': {
            'description': '主要针对母语为英语的学生，使用更加复杂和专业化的词汇，需要更广泛的词汇量',
            'reading_speed': '200-300个单词/分钟'
        }
    },
    'grades': {
        'pass': {
            'language_use': '提供清晰的语言和例子如简单的故事、日常生活中常见话题，来帮助学生理解',
            'visual_aid': '使用图像来可视化概念，建立直观的连接'
        },
        'merit': {
            'in_depth_explanation': '提供更深入的解释，包括相关背景知识；提供实例和案例研究，引导学生思考概念的不同方面和可能的应用场景',
            'visual_aid': '使用图像来可视化概念，建立直观的连接'
        },
        'distinction': {
            'in_depth_explanation': '提供更深入的解释，包括相关背景知识；提供实例和案例研究，引导学生思考概念的不同方面和可能的应用场景',
            'independent_thinking': '鼓励学生进行独立思考和探索性学习，提供开放性和前沿领域研究的例子，让他们应用概念来解决现实问题'
        }
    },
    'additional_resources': {
        'pass': {
            'explanation_and_examples': 'google'
        },
        'merit': {
            'explanation_and_examples': 'google',
            'recommended_courses': 'youtube, mit opencouseware, stanford课程资料，coursera, edX中质量top的课程内容，最好能一句话概括课程summary'
        },
        'distinction': {
            'explanation_and_examples': 'google',
            'recommended_courses': 'youtube, mit opencouseware, stanford课程资料，coursera, edX中质量top的课程内容，最好能一句话概括课程summary',
            'cutting_edge_research': 'arxiv'
        }
    }
    }
    if reading_level:
        reading_info = education_resources['reading_levels'].get(reading_level, {})
    
    else: reading_info = None
    if grade_level:
        grade_info = education_resources['grades'].get(grade_level, {})
        additional_resources = education_resources['additional_resources'].get(grade_level, {})
    else:
        grade_info, additional_resources = None, None
    
    full_sentence = f'''You are a very experienced teacher, adept at summarizing and providing 
    more in-depth explanations with the materials given by students. 
    Your students' reading level is {reading_info.get('description', '')}, 
    and they aim to reach the level of {grade_info}. 
    You can also provide some more detailed information at {additional_resources}. 
    Enclose all mathematical formulas within double dollar signs($$), for example: $$e^{{i\\pi}} + 1 = 0$$.
    Integrate this information and return it in markdown format as follows:
    # Summary
    Abstract of the content of the lecture notes... Abstract of the content of the
    lecture notes... Abstract of the content of the lecture notes... Abstract of the
    content of the lecture notes... Abstract of the content of the lecture notes..
    Abstract of the content of the lecture notes... Abstract of the content of the
    lecture notes..
    # Concept 1
    ## Definition

    Basically the original text... Basically the original text. Basically the original
    text... Basically the original text... Basically the original text... Basically the
    original text... Basically the original text... Basically the original text..
    Basically the original text... Basically the original text..

    ## Explanation

    Explanation of the concept corresponding to user's reading level.
    Explanation of the concept corresponding to user's reading level..
    Explanation of the concept corresponding to user's reading level..

    # Concept 2
    # Definition
    Basically the original text... Basically the original text... Basically the original
    text... Basically the original text... Basically the original text. Basically the
    original text... Basically the original text... Basically the original......'''
    return full_sentence

def page_one():
    # Title of the application
    st.title("AiTA demo 0.0.1")
    st.subheader("AI-powered 7/24 tutoring system designed for college students")
    st.sidebar.subheader('ATA - online tutoring system')
    st.sidebar.markdown("""ATA (Artificial Intelligence Tutoring
    Assistant) is an innovative online
    tutoring system designed specifically for
    college students.""")
    st.sidebar.markdown(' ')
    st.sidebar.markdown("Made by [XuyingLi](#)")
    st.sidebar.markdown("### Key Features:")
    st.sidebar.markdown("""
    1. **Lecture Notes Digest**: The system utilizes language processing model to generate easy-to-understand and organized lecture notes digests.
    2. **Question Sheet Solutions**: By uploading their question sheets, students can receive step-by-step solutions and explanations generated by the AI system.
    3. **Q&A Bot**: AiTA is equipped with a smart Q&A bot that provides instant answers to students' questions.
    """)
    st.sidebar.markdown("[Source code](#) can be found here.")
    st.sidebar.markdown("[Join Discord](#) to keep updated and get instant tech support.")

    # Containers for layout

    study_option = st.radio("I will be studying on:", ('Lecture materials', 'Question sheets'))
    col1, col2 = st.columns(2)
    # Column 1 for lecture materials
    with col1:
        st.write("Lecture notes")
        st.session_state.lecture_notes_file = st.file_uploader("", type=['pdf'])

        st.session_state.reading_level = st.select_slider('Reading level:', options=['Elementary', 'Intermediate', 'Advanced'],value=('Intermediate'))

        st.session_state.teaching_style = st.selectbox("Teaching style of the tutor", ['Interactive style', 'Lecture style', 'Guided discovery'])

    # Column 2 for question sheets
    with col2:
        st.write("Question sheets (optional but highly recommended)")
        st.session_state.question_sheets_file = st.file_uploader(" ", type=['pdf'])

        st.session_state.grade_level = st.select_slider('My current level of grade:', options=['Pass or lower', 'Merit', 'Distinction'],value=('Merit'))

        st.session_state.tone_of_conversation = st.selectbox("Tone of the conversation:", ['Encouraging', 'Formal', 'Casual'])

    col3, col4, colx = st.columns([3,3,7])
    # Button to initiate processing
    with col3:
        st.session_state.language =  st.selectbox('Language:', ['English', 'Chinese'])
        if st.button('Generate') and (st.session_state.lecture_notes_file or st.session_state.question_sheets_file):
            st.session_state.page = "two"
            if st.session_state.lecture_notes_file:
                with pdfplumber.open(st.session_state.lecture_notes_file) as pdf:
                    pages = [page.extract_text() for page in pdf.pages]
                full_text_d = "\n".join(pages)
                with open("document.txt", "w") as text_file:
                    text_file.write(full_text_d)
                st.session_state.lecture_notes_file = True
            if st.session_state.question_sheets_file:
                with pdfplumber.open(st.session_state.question_sheets_file) as pdf:
                    pages = [page.extract_text() for page in pdf.pages]
                full_text_q = "\n".join(pages)
                with open("question.txt", "w") as text_file:
                    text_file.write(full_text_q)
                st.session_state.question_sheets_file = True

def get_text():
    input_text = st.text_input("You: ","Hello", key="input")
    return input_text

def page_two():
    progress_text = "Operation in progress. Please wait."
    # Initialize variables
    full_text_d = ""
    full_text_q = ""
    
    my_bar = st.progress(0, text=progress_text)
    my_bar.progress(20, text=progress_text)
    document_path = 'document.txt'
    if os.path.exists(document_path):
        with open(document_path, 'r', encoding='utf-8') as file:
            full_text_d = file.read()

    # Check if question.txt exists and read its content
    question_path = 'question.txt'
    if os.path.exists(question_path):
        with open(question_path, 'r', encoding='utf-8') as file:
            full_text_q = file.read()
            
    my_bar.progress(40, text=progress_text)
    system_message = create_prompt(st.session_state.reading_level, st.session_state.grade_level)
    my_bar.progress(80, text=progress_text)
    if full_text_d and full_text_q:
        messages =  [
                            {'role':'system',
                            'content': system_message},
                            {'role':'user',
                            'content': f"【{full_text_d}】【{full_text_q}】"},]
    elif full_text_d:
        messages =  [
                            {'role':'system',
                            'content': system_message},
                            {'role':'user',
                            'content': f"【{full_text_d}】"},]
    elif full_text_q:
        messages =  [
                            {'role':'system',
                            'content': system_message},
                            {'role':'user',
                            'content': f"【{full_text_q}】"},]

    my_bar.progress(90, text=progress_text)
    response = get_completion_from_messages(messages)
    my_bar.empty()
    col1, col2 = st.columns(2)

    with col1:
        st.subheader('Generated material')
        st.markdown(response)

    with col2:
        st.subheader('Q&A Chatbot')
        user_input = get_text()
        system_message_1 = """
        answer the question with patent and give examples
        """
        if user_input:
            messages =  [
                            {'role':'system',
                            'content': system_message_1},
                            {'role':'user',
                            'content': f"【{user_input}】"},]
            output = get_completion_from_messages(messages)
            # store the output 
            st.session_state.past.append(user_input)
            st.session_state.generated.append(output)
        if st.session_state['generated']:
            for i in range(len(st.session_state['generated'])-1, -1, -1):
                message(st.session_state["generated"][i], key=str(i))
                message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')

def main():
    # Storing the chat
    if 'generated' not in st.session_state:
        st.session_state['generated'] = []

    if 'past' not in st.session_state:
        st.session_state['past'] = []

    if "openai_model" not in st.session_state:
            st.session_state["openai_model"] = "gpt-4-1106-preview"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "messages_display" not in st.session_state:
        st.session_state.messages_display = []

    if "page" not in st.session_state:
        st.session_state.page = "one"

    if "reading_level" not in st.session_state:
        st.session_state.reading_level = ""
    
    if "teaching_style" not in st.session_state:
        st.session_state.teaching_style = "English"

    if "language" not in st.session_state:
        st.session_state.language = "English"

    if "grade_level" not in st.session_state:
        st.session_state.grade_level = '5'

    if "material" not in st.session_state:
        st.session_state.lecture_notes_file = None
        st.session_state.question_sheets_file = None
    
    if "tone_of_conversation" not in st.session_state:
        st.session_state.tone_of_conversation = ''


    # 根据session状态来渲染页面
    if st.session_state.page == "one":
        page_one()
    elif st.session_state.page == "two":
        page_two()
    
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    main()
