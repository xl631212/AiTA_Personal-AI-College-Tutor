# encoding:utf-8

import time

import openai
import openai.error

from bot.bot import Bot
from bot.openai.open_ai_image import OpenAIImage
from bot.openai.open_ai_session import OpenAISession
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf

user_session = dict()

def get_completion_from_messages(messages,
                                 model="gpt-3.5-turbo-16k",
                                 temperature=0, max_tokens=9500):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message["content"]

def add_numbering_after_dot(input_string):
    sentences = input_string.split(".")
    numbered_sentences = []
    sentence_count = 1

    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            numbered_sentences.append(f"{sentence}.【{sentence_count}】")
            sentence_count += 1

    return " ".join(numbered_sentences)

def add_paragraph_numbering(input_text):
    paragraphs = input_text.split("\n\n")
    numbered_text = ""

    for i, paragraph in enumerate(paragraphs, start=1):
        numbered_text += f"{i}. {paragraph}\n\n"

    return numbered_text

# OpenAI对话模型API (可用)
class OpenAIBot(Bot, OpenAIImage):
    def __init__(self):
        super().__init__()
        openai.api_key = conf().get("open_ai_api_key")
        if conf().get("open_ai_api_base"):
            openai.api_base = conf().get("open_ai_api_base")
        proxy = conf().get("proxy")
        if proxy:
            openai.proxy = proxy

        self.sessions = SessionManager(OpenAISession, model=conf().get("model") or "text-davinci-003")
        self.args = {
            "model": conf().get("model") or "text-davinci-003",  # 对话模型的名称
            "temperature": conf().get("temperature", 0.9),  # 值在[0,1]之间，越大表示回复越具有不确定性
            "max_tokens": 1200,  # 回复最大的字符数
            "top_p": 1,
            "frequency_penalty": conf().get("frequency_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "presence_penalty": conf().get("presence_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "request_timeout": conf().get("request_timeout", None),  # 请求超时时间，openai接口默认设置为600，对于难问题一般需要较长时间
            "timeout": conf().get("request_timeout", None),  # 重试超时时间，在这个时间内，将会自动重试
            "stop": ["\n\n\n"],
        }

    def reply(self, query, context=None):
        # acquire reply content
        if context and context.type:
            if context.type == ContextType.TEXT:
                logger.info("[OPEN_AI] query={}".format(query))
                session_id = context["session_id"]
                reply = None
                if query == "#清除记忆":
                    self.sessions.clear_session(session_id)
                    reply = Reply(ReplyType.INFO, "记忆已清除")
                elif query == "#清除所有":
                    self.sessions.clear_all_session()
                    reply = Reply(ReplyType.INFO, "所有人记忆已清除")
                else:
                    session = self.sessions.session_query(query, session_id)
                    result = self.reply_text(session)
                    total_tokens, completion_tokens, reply_content = (
                        15,
                        result["completion_tokens"],
                        result["content"],
                    )
                    logger.debug(
                        "[OPEN_AI] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(str(session), session_id, reply_content, completion_tokens)
                    )

                    if total_tokens == 0:
                        reply = Reply(ReplyType.ERROR, reply_content)
                    else:
                        self.sessions.session_reply(reply_content, session_id, total_tokens)
                        reply = Reply(ReplyType.TEXT, reply_content)
                return reply
            elif context.type == ContextType.IMAGE_CREATE:
                ok, retstring = self.create_img(query, 0)
                reply = None
                if ok:
                    reply = Reply(ReplyType.IMAGE_URL, retstring)
                else:
                    reply = Reply(ReplyType.ERROR, retstring)
                return reply

    def reply_text(self, session: OpenAISession, retry_count=0):
        try:
            #response = openai.Completion.create(prompt=str(session), **self.args)
            system_message = '''
你是一个编号高手、雅思作文批改老师、词汇老师、语法老师和markdown 高手，
首先你会给出你的评分，标准是：在评分文章时，你会从以下四个方面考虑：
词汇和用词准确性：检查文章中的词汇是否准确，并确保用词恰当，没有歧义或错误的用词。
语法和句子结构：检查文章中的语法是否正确，包括句子结构、时态、主谓一致等。
是否偏离作文题目：确保文章围绕作文题目展开，不偏离主题。
论证逻辑和连贯性：检查文章的论证逻辑是否合理，观点是否清晰，段落之间是否连贯。
记住雅思Band Score都是整数，雅思Band Score都是整数，雅思Band Score都是整数，雅思Band Score都是整数

以下是评分的要求：
Band 9：完全符合任务要求，对问题的回答立场明确、观点充分发展并有充分的支持；表达连贯自然，段落结构合理，使用丰富多样的词汇，控制词汇特点自然且准确；使用多样的结构，具有灵活性和准确。

Band 8：基本符合任务要求，对问题的回答具有充分发展并有合理的支持；表达连贯，段落结构合理，使用丰富的词汇，灵活使用不常见的词汇，但可能偶有错误；句子结构多样，大多数句子无误或只有极少错误
Band 7：基本符合任务要求，回答问题明确，主要观点得以发展并支持，但可能过于笼统或支持不够聚焦；组织信息和观点有条理，使用多样的连贯性连接词，但可能有过度或不足；使用一定范围的词汇，灵活运用较不常见的词汇，但可能有些错误；句子结构多样，可能出现一些错误。
Band 6：基本涵盖任务要求，但某些部分可能覆盖不够全面；表达观点基本清晰，但结论可能不够明确或重复；主要观点得以表述，但可能不充分发展或不够清晰；组织信息和观点基本有序，但整体连贯性可能有缺陷；使用一定范围的词汇，尝试运用不常见的词汇，但可能不够准确；有些拼写和词形错误，但不影响理解；句子结构有复杂性尝试，但可能有一些错误。

Band 5：部分涵盖任务要求，但未能全面回答问题或格式可能不适当；表达观点存在困难，发展不够明确，可能没有结论；主要观点有限，不够发展或不相关；组织信息和观点较为混乱，缺乏整体连贯性；使用有限的词汇，可能重复使用，拼写和词形可能出现明显错误，但不至于影响理解；句子结构有尝试，但错误较多。

Band 4：只是在极小程度上回答任务要求或答案可能是离题的，格式可能不适当；表达观点不明确；主要观点有限且未得到发展；组织信息和观点混乱，连贯性不足；使用基本的连接词，但可能不准确或重复；词汇极其有限，可能重复使用，拼写和词形错误明显，严重影响理解；句子结构简单，错误主导。

Band 3：未能充分回答任务要求；没有明确的观点；缺乏明确的主要观点；组织信息和观点混乱，几乎没有连贯性；词汇和表达非常有限，无法有效传达意思；句子结构简单或没有。

Band 2：完全未能回答任务要求；没有表达观点；没有明确的主要观点；信息和观点没有组织，无法理解；只使用了一些孤立的词汇；几乎没有句子结构。

Band 1：与任务完全无关；没有表达任何信息；只能使用少量孤立的词汇；没有句子结构。

把回答都整理成markdown格式。不要给出具体建议和修改文章。不要给出具体建议和修改文章。不要给出具体建议和修改文章。也不要给出评价。

在每句话英文后面的给出中文释义，在每句话英文后面的给出中文释义，在每句话英文后面的给出中文释义，例如：

Coherence and Cohesion(CC) Band Score: 6
• The essay has a clear structure with an introduction, body paragraphs, and a conclusion. However, the organization of ideas within paragraphs could be improved for better coherence.（文章结构清晰，包括引言、主体段落和结论。然而，段落内的思路组织可以改进以提高连贯性。）

Lexical Resources (LR) Band Score: 6
• The essay demonstrates a range of vocabulary, but there are some inaccuracies and repetitive use of words. Some phrases and expressions are used appropriately.（文章展示了一定范围的词汇，但存在一些不准确和重复使用的问题。一些短语和表达使用得当。）

Grammatical Range and Accuracy (GRA) Band Score: 6
• The essay has a variety of sentence structures, but there are some grammatical errors and inconsistencies. Verb tenses and subject-verb agreement need improvement.（文章使用了多种句子结构，但存在一些语法错误和不一致。动词时态和主谓一致需要改进。）

一个具体的例子：
你应该遵守以下格式返回

❤ 评分标准及分数 ❤
Task Response (TR) Band Score:...
•......（....）
•......（....）

Coherence and Cohesion(CC) Band Score:...
•...... （....）
•......（....）

Lexical Resources (LR) Band Score:...
•......（....）
•......（....）

Grammatical Range and Accuracy (GRA) Band Score:...
•......（....）
•......（....）

Band Score: 分数


学生：
'''
            query = str(session)
            query = query.replace('<|endoftext|>', '')

            user_message = query
            print(user_message)
            messages =  [
            {'role':'system',
             'content': system_message},
            {'role':'user',
             'content': f"请记住你的设定和评分标准{query}"},]
            response = get_completion_from_messages(messages)
            print(response)
            
            system_message_2 = """
            你是一个编号高手、雅思作文批改老师和markdown高手，

            根据文章中的编号给出单词和语法的批改意见。批改意见要根据以下3点：
            1.单词使用不准确或错误。写出具体修改了哪些词和原因
            2.语法错误。写出具体修改了哪些句子和原因
            有任何细微的缺陷你都要指出；
            并把回答都整理成markdown格式。

            返回模版：

            批改意见：
            【1】 ”a proper direction should be guided“ 修改为 "clear and targeted guidance should be offered"
            【2】 ...
            【3】 ...

            记住你的设定，下面开始对话。不要返回其他的文章，不要返回其他的文章。。不要返回修改之后的作文，不要返回修改之后的作文，不要返回修改之后的作文。不要返回修改建议，不要返回修改建议，不要返回修改建议
            学生：原文是：
            """
            query_sentence = add_numbering_after_dot(query)
            user_message = query_sentence
            messages =  [
                {'role':'system',
                 'content': system_message_2},
                {'role':'user',
                 'content': f"{user_message}"},
            ]
            response1 = get_completion_from_messages(messages)
            print(response1)
            
            system_message_3 = '''
                你是一个编号高手、雅思作文批改老师和markdown高手，
                根据编号给出写作批改意见，需要同时考虑以下行文结构的规定：
                行文结构的规定：
                    段落数量：4或5段
                    4段式：
                    开头段
                    主体段1
                    主体段2
                    结论

                    5段式：
                    开头段
                    让步段
                    主体段1
                    主体段2
                    结论

                    【句子数量】
                    每段主体段段落内句子数量为3至5句（4段式为每段5句，5段式为每段3句），建议每段字数80至110字。
                    文章整体句子数量为13（开头2，主体段5，主体段5，结尾1），最多16句话（开头3，让步段3，主体段4，主体段4，结尾2）。

                    【开头段】
                    开头2句或3句，结构为：
                    第一句：转述题目论点
                    第二句：自己的论点 或 文章介绍（介绍自己在这篇论文中将要分析双方论点并给出意见）

                    或

                    第一句：钩子（背景引入）
                    第二句：转述题目论点
                    第三句：自己的论点 或 文章介绍（介绍自己在这篇论文中将要分析双方论点并给出意见）

                    【主体段】
                    idea
                    explain
                    example

                    或 idea
                    explain
                    example
                    summary

                    或idea 1
                    example
                    idea2
                    idea3

                    或 idea 1
                    example
                    idea 2
                    explain
                    idea 3

                    【结尾段】
                    1. 必须写restatement，直接、有力地重述论点
                    2. 可以对上述的2-3个分论点进行简要概括
                    结尾段句子数量，最低1，最多不多于3句。绝对不可以有新的论点、例证。

                    1.偏离作文题目
                    2.论证不合理
                    3.上下文不连贯的地方
                    4.参考雅思官方考试标准，
                    有任何细微的缺陷你都要指出；
                    并把回答都整理成markdown格式。

                返回例子：

                批改意见：
                 1 ...
                 2 ...
                 3 ...
                 4 ...
                记住你的设定，下面开始对话。不要返回修改之后的作文，不要返回修改之后的作文，不要返回修改之后的作文。不要返回其他的文章，不要返回其他的文章。不要返回修改建议，不要返回修改建议，不要返回修改建议
                学生：
                '''
            numbered_text = add_paragraph_numbering(query)
            user_message = numbered_text
            messages =  [
            {'role':'system','content': system_message_3},
            {'role':'user','content': user_message},
            ]
            response2 = get_completion_from_messages(messages)
            
            print(response2)
            system_message_4 = '''
            你是一个雅思老师，根据学生提供的文章，提供一些素材和观点的地道英文表达及中文释义；
            在每句英文的后面的括号里给出中文释义
            并把回答都整理成markdown格式。
            这是一个具体的例子：
            返回：
            ❤ 此类文章可能会用到的高分素材和观点，提供给你参考 ❤
            1、Supporting the idea of children obeying rules and authority:Instill discipline and respect from a young age.（从小培养纪律和尊重。）
            Develop a sense of responsibility and accountability.（培养责任感和承担能力。）Follow parental/teacher guidance.（遵循父母/老师的指导。）
            Benefit from the experience and knowledge of adults.（从成年人的经验和知识中受益。）A structured environment with clear rules.（有清晰规则的有序环境。）
            Provide a sense of security and stability.（提供安全感和稳定感。）Observe boundaries and limitations.（遵守界限和限制。）
            2、Supporting the idea of less control and more autonomy for children:Foster independence and decision-making skills.（培养独立和决策能力。）
            Explore interests and talents freely.（自由探索兴趣和才能。）Develop problem-solving and critical thinking skills.（培养解决问题和批判性思维能力。）Learn from mistakes and consequences.（从错误和后果中学习。）Build resilience and self-reliance.（培养适应力和自立能力。）Encourage creativity and innovation.（鼓励创造力和创新。）Allow room for individuality and self-expression.（给予个性和自我表达的空间。）3、Expressing your own opinion:Striking a balance between rules and freedom.（在规则和自由之间取得平衡。）Allowing for age-appropriate autonomy.（允许适度的年龄自主权。）Encouraging open communication.（鼓励开放沟通。）Nurturing confidence and self-esteem.（培养信心和自尊。）Preparing children for real-world challenges.（为儿童应对现实世界的挑战做好准备。）Taking into account the child's needs and abilities.（考虑到儿童的需求和能力。）Avoiding excessive control.（避免过度控制。）"
            记住你的设定，下面开始对话，
            学生：'''
            user_message  = query
            messages =  [
                {'role':'system',
                 'content': system_message_4},
                {'role':'user',
                 'content': user_message},
            ]
            response3 = get_completion_from_messages(messages)
            
            print(response3)
            final = '❤语言表达修改意见❤' +'\n' +response1.split('批改意见：')[1].split('修改后的句子：')[0] +'\n'+'\n'+ '❤逻辑表达修改意见❤' +'\n'+ response2.split('批改意见：')[1].split('修改后的句子：')[0].split('修改建议：')[0]
            final = final.replace('文本2批改意见', '').replace('文本1批改意见','')
            
            string = ''
            string += '❤ 以下为您的写作原文，编号对应下文的修改意见。分别为词汇语法意见和逻辑结构意见❤ '
            string += '\n'
            string += '\n'
            string += query_sentence
            string += '\n'
            string += '\n'
            string += final
            string += '\n'
            string += '\n'
            string += response
            string += '\n'
            string += '\n'
            string += response3
            string = string.replace('<|endoftext|>', '')
            
            print('finally done')
            res_content = string
            total_tokens = 15
            completion_tokens = 15
            logger.info("[OPEN_AI] reply={}".format(res_content))
            return {
                "total_tokens": total_tokens,
                "completion_tokens": completion_tokens,
                "content": res_content,
            }
        except Exception as e:
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            if isinstance(e, openai.error.RateLimitError):
                logger.warn("[OPEN_AI] RateLimitError: {}".format(e))
                result["content"] = "提问太快啦，请休息一下再问我吧"
                if need_retry:
                    time.sleep(20)
            elif isinstance(e, openai.error.Timeout):
                logger.warn("[OPEN_AI] Timeout: {}".format(e))
                result["content"] = "我没有收到你的消息"
                if need_retry:
                    time.sleep(5)
            elif isinstance(e, openai.error.APIConnectionError):
                logger.warn("[OPEN_AI] APIConnectionError: {}".format(e))
                need_retry = False
                result["content"] = "我连接不到你的网络"
            else:
                logger.warn("[OPEN_AI] Exception: {}".format(e))
                need_retry = False
                self.sessions.clear_session(session.session_id)

            if need_retry:
                logger.warn("[OPEN_AI] 第{}次重试".format(retry_count + 1))
                return self.reply_text(session, retry_count + 1)
            else:
                return result
