from openai import OpenAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain_core.prompts.few_shot import FewShotPromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from model import get_all_contents, add_chat, update_chat
import os
from langchain import hub
import json
from config import OPENAI_API_KEY, LANGSMITH_API_KEY

os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
os.environ['LANGSMITH_API_KEY'] = LANGSMITH_API_KEY

VECTORSTORE_PATH = "vectorstore.faiss"

def initialize_vectorstore():
    sections = get_all_contents()

    # RecursiveCharacterTextSplitter 사용
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100 
    )
    
    # 섹션을 분할하여 문서 리스트 생성
    documents = []
    for section in sections:
        splits = text_splitter.split_text(section)
        documents.extend([Document(page_content=split) for split in splits])

    # 문서에 대한 임베딩 생성 및 벡터스토어 초기화
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(documents, embeddings)

    # 벡터스토어를 로컬에 저장
    vectorstore.save_local(VECTORSTORE_PATH)
    return vectorstore

def get_relevant_sections(user_input):
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.load_local(VECTORSTORE_PATH, embeddings, allow_dangerous_deserialization=True)

    # 가장 유사한 결과를 찾으면서 결과 간의 중복을 최소화. 유사성과 다양성을 동일하게 고려
    retriever = vectorstore.as_retriever(search_type="mmr", k=5, lambda_mult=0.5)
    
    relevant_documents = retriever.invoke(user_input)
    relevant_sections = "\n".join([doc.page_content for doc in relevant_documents])

    return relevant_sections

def get_ai_response(user_input, chat_history):

    # Few-Shot 프롬프트 가져오는 부분
    with open('few_shot_prompts.json', 'r', encoding='utf-8') as f:
        few_shot_prompts = json.load(f)

    # LangSmith Hub에서 Prompt 가져오는 부분
    hub_prompt_template = hub.pull("kdt-team3/kdt-team3")

    # 컨텍스트를 가져오는 부분
    context = get_relevant_sections(user_input)

    # LLM 생성
    llm = ChatOpenAI(model_name="gpt-4o-mini-2024-07-18", temperature=0)

    # 예제 프롬프트 생성
    example_prompt_template = PromptTemplate(
        input_variables=["prompt", "completion"],
        template="Q: {prompt}\nA: {completion}"
    )

    few_shot_prompt_template = FewShotPromptTemplate(
        examples=few_shot_prompts,
        example_prompt=example_prompt_template,
        prefix=hub_prompt_template.template,  # Hub에서 가져온 템플릿의 텍스트 사용
        suffix="{context}\n질문: {chat_history}\n{human_input}\n",
        input_variables=["context", "human_input", "chat_history"],
    )

    formatted_prompt = few_shot_prompt_template.format(
        context=context, 
        human_input=user_input,
        chat_history=chat_history
    )

    response = llm(formatted_prompt)

    # 질문 및 응답에서 \n이 있으면 <br>로 변환
    ai = response.content.replace("\n", "<br>")
    user = user_input.replace("\n", "<br>")

    return ai, user