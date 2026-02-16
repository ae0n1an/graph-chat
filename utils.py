import os
import openai
import streamlit as st
from datetime import datetime
from streamlit.logger import get_logger
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

logger = get_logger('Langchain-Chatbot')

#decorator
def enable_chat_history(func):
    # to clear chat history after swtching chatbot
    current_page = func.__qualname__
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = current_page
    if st.session_state["current_page"] != current_page:
        try:
            st.cache_resource.clear()
            del st.session_state["current_page"]
            del st.session_state["messages"]
        except:
            pass

    # to show chat history on ui
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": "Please ask me anything about MyThanks!"}]
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if "fig" in msg:
                st.plotly_chart(msg["fig"], use_container_width=True)

    def execute(*args, **kwargs):
        func(*args, **kwargs)
    return execute

def display_msg(msg, author):
    """Method to display message on the UI

    Args:
        msg (str): message to display
        author (str): author of the message -user/assistant
    """
    if "messages" not in st.session_state:
        st.session_state.messages = []
    st.session_state.messages.append({"role": author, "content": msg})
    st.chat_message(author).write(msg)

def choose_custom_openai_key():
    openai_api_key = st.sidebar.text_input(
        label="OpenAI API Key",
        type="password",
        placeholder="sk-...",
        key="SELECTED_OPENAI_API_KEY"
        )
    if not openai_api_key:
        st.error("Please add your OpenAI API key to continue.")
        st.info("Obtain your key from this link: https://platform.openai.com/account/api-keys")
        st.stop()

    model = "gpt-4o-mini"
    try:
        client = openai.OpenAI(api_key=openai_api_key)
        available_models = [{"id": i.id, "created":datetime.fromtimestamp(i.created)} for i in client.models.list() if str(i.id).startswith("gpt")]
        available_models = sorted(available_models, key=lambda x: x["created"])
        available_models = [i["id"] for i in available_models]

        model = st.sidebar.selectbox(
            label="Model",
            options=available_models,
            key="SELECTED_OPENAI_MODEL"
        )
    except openai.AuthenticationError as e:
        st.error(e.body["message"])
        st.stop()
    except Exception as e:
        print(e)
        st.error("Something went wrong. Please try again later.")
        st.stop()
    return model, openai_api_key

def choose_azure_openai_config():
    with st.sidebar.expander("Azure OpenAI Configuration", expanded=True):
        azure_api_key = st.text_input("Azure API Key", type="password", key="AZURE_OPENAI_API_KEY_INPUT")
        azure_endpoint = st.text_input("Azure Endpoint", placeholder="https://your-resource.openai.azure.com/", key="AZURE_OPENAI_ENDPOINT_INPUT")
        azure_deployment = st.text_input("Deployment Name", key="AZURE_OPENAI_DEPLOYMENT_NAME_INPUT")
        azure_api_version = st.text_input("API Version", value="2024-02-01", key="AZURE_OPENAI_API_VERSION_INPUT")

    if not (azure_api_key and azure_endpoint and azure_deployment):
        st.error("Please provide all Azure OpenAI configuration details.")
        st.stop()
    
    return {
        "api_key": azure_api_key,
        "azure_endpoint": azure_endpoint,
        "azure_deployment": azure_deployment,
        "api_version": azure_api_version
    }

def configure_llm():
    available_llms = ["gpt-4o-mini", "Azure OpenAI"]
    llm_opt = st.sidebar.radio(
        label="LLM",
        options=available_llms,
        key="SELECTED_LLM"
        )

    if llm_opt == "gpt-4o-mini":
        llm = ChatOpenAI(model_name=llm_opt, temperature=0, streaming=True, api_key=st.secrets.get("OPENAI_API_KEY"))
    elif llm_opt == "Azure OpenAI":
        # Check secrets first, then fallback to sidebar
        if all(k in st.secrets for k in ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT_NAME"]):
            llm = AzureChatOpenAI(
                azure_deployment=st.secrets["AZURE_OPENAI_DEPLOYMENT_NAME"],
                openai_api_version=st.secrets.get("AZURE_OPENAI_API_VERSION", "2024-02-01"),
                azure_endpoint=st.secrets["AZURE_OPENAI_ENDPOINT"],
                api_key=st.secrets["AZURE_OPENAI_API_KEY"],
                temperature=0,
                streaming=True
            )
        else:
            config = choose_azure_openai_config()
            llm = AzureChatOpenAI(
                azure_deployment=config["azure_deployment"],
                openai_api_version=config["api_version"],
                azure_endpoint=config["azure_endpoint"],
                api_key=config["api_key"],
                temperature=0,
                streaming=True
            )
    else:
        model, openai_api_key = choose_custom_openai_key()
        llm = ChatOpenAI(model_name=model, temperature=0, streaming=True, api_key=openai_api_key)
    return llm

def print_qa(cls, question, answer):
    log_str = "\nUsecase: {}\nQuestion: {}\nAnswer: {}\n" + "------"*10
    logger.info(log_str.format(cls.__name__, question, answer))

@st.cache_resource
def configure_embedding_model():
    embedding_model = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    return embedding_model

def sync_st_session():
    for k, v in st.session_state.items():
        st.session_state[k] = v
