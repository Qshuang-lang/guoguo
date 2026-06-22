import streamlit as st
import os
from openai import OpenAI
import datetime
import json

from streamlit import session_state

#设置页面配置项
st.set_page_config(
    page_title="AI智能伴侣",
    page_icon="🤔",
    layout="wide",#布局
    initial_sidebar_state="expanded",#控制的是侧边栏的状态
    menu_items={}
)

#生成会话标识的函数
def generate_session_name():
    return datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

#保存会话信息函数
def save_session():
    if st.session_state.current_session:
        #构建新的会话对象
        session_data = {
            "nick_name": st.session_state.nick_name,
            "nature": st.session_state.nature,
            "current_session": st.session_state.current_session,
            "messages": st.session_state.messages
        }

        # 如果session 目录不存在，则创建
        if not os.path.exists("session"):
            os.mkdir("session")

        # 保存会话数据
        with open(f"session/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
#用来加载所有会话列表
def load_sessions():
    session_list=[]
    #加载所有会话列表
    if os.path.exists("session"):
        file_list=os.listdir("session")
        for filename in file_list:
            if filename.endswith(".json"):
                session_list.append(filename[:-5])
    return session_list


#加载指定会话信息
def load_session(session_name):
    try:
        if os.path.exists(f"session/{session_name}.json"):
            #读取会话数据
            with open(f"session/{session_name}.json","r",encoding="utf-8")as f:
                session_data=json.load(f)
                st.session_state.messages=session_data["messages"]
                st.session_state.nick_name = session_data["nick_name"]
                st.session_state.nature = session_data["nature"]
                st.session_state.current_session = session_name
    except Exception:
        st.error(f"加载会话失败")

#删除会话信息函数
def delete_session(session_name):
    try:
        if os.path.exists(f"session/{session_name}.json"):
            os.remove(f"session/{session_name}.json")#删除文件
            if session_name==st.session_state.current_session:
                st.session_state.messages=[]
                st.session_state.current_session=generate_session_name()
    except Exception:
        st.error(f"删除会话失败")


    # 大标题
st.title("AI智能伴侣")

# logo
import os
from PIL import Image
base_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(base_dir, "resource", "logo.png")
if os.path.exists(logo_path):
    st.logo(Image.open(logo_path))

# 系统提示词
system_prompt = """
        你叫%s，现在是用户的伴侣，请完全代入伴侣角色。
        规则:
             1. 每次只回1条消息
             2. 禁止任何场景或状态描述性文字
             3. 匹配用户的语言
             4. 回复简短，像微信聊天一样
             5. 可以用❤等emoji表情
             6. 用符合伴侣性格的方式对话
             7. 充分体现伴侣性格特征
        伴侣性格：%s
        
        严格遵守规则回复！
"""

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []
#昵称
if "nick_name" not in st.session_state:
    st.session_state.nick_name = "小美"
#性格
if "nature" not in st.session_state:
    st.session_state.nature = "可爱活泼女孩"
#会话标识
if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_name()

# 展示历史聊天记录
st.text(f"会话名称:{st.session_state.current_session}")
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])

# AI客户端
client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'),base_url="https://api.deepseek.com")


# 左侧边栏设置
with st.sidebar:
    #会话信息
    st.title("ai控制面板")

    #新建会话按钮
    if st.button("新建会话",width="stretch",icon="🔋"):
        #1,保存当前会话信息
        save_session()

        #2.创建一个新的会话
        if st.session_state.messages:#如果有消息，则保存
            st.session_state.messages=[]
            st.session_state.current_session = generate_session_name()
            save_session()
            st.rerun()#重新运行当前页面


#会话历史
    st.text("会话历史")
    session_list=load_sessions()
    for session in session_list:
        col1,col2=st.columns([4,1])
           #加载会话信息
        with col1:
            #三元运算符: 条件?真值:假值
            if st.button(session,width="stretch",icon="🐵",key=f"load_{session}",type="primary" if session==st.session_state.current_session else "secondary"):
                load_session(session)
                st.rerun()
            #删除会话信息
        with col2:
            if st.button("",width="stretch",icon="❌",key=f"delete_{session}"):
                delete_session(session)
                st.rerun()

    #伴侣信息
    st.title("伴侣信息")
    #昵称输入框
    nick_name = st.text_input("昵称", placeholder="请输入伴侣昵称", value=st.session_state.nick_name)
    if nick_name:
        st.session_state.nick_name = nick_name

#性格输入框
    nature = st.text_area("性格", placeholder="请输入伴侣性格", value=st.session_state.nature)
    if nature:
        st.session_state.nature = nature

# 聊天输入框
prompt = st.chat_input("请输入你的问题")
if prompt:
    # 显示用户消息
    st.chat_message("user").write(prompt)
    print("---------->调用AI大模型,提示词",prompt)
        #保存用户输入的提示词
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 调用Ai大模型
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt % (st.session_state.nick_name, st.session_state.nature)},
            *st.session_state.messages
        ],
        stream=True
    )

#输出大模型返回的结果（流式输出）
    response_message = st.empty()

    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content=chunk.choices[0].delta.content
            full_response+=content
            response_message.chat_message("assistant").write(full_response)

#保存大模型返回值
    st.session_state.messages.append({"role": "assistant", "content": full_response})

#保存会话信息
    save_session()


