import utils
import sqlite3
import streamlit as st
from pathlib import Path
from sqlalchemy import create_engine

from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.tools import Tool
from langchain.memory import ConversationBufferMemory
import plotly.express as px
import pandas as pd
from langchain_openai import ChatOpenAI

# Set page config for the Chat page
st.set_page_config(page_title="MyThanks Chatbot - Chat", page_icon="🛒", layout="wide")

# Styling to refine the chat UI
st.markdown(
    """
    <style>
        /* Hide default sidebar nav if we want a clean look */
        [data-testid="stSidebarNav"] {
            display: none;
        }

        /* Sidebar Width Adjustment */
        section[data-testid="stSidebar"] {
            width: 500px !important;
            # min-width: 500px !important;
            # max-width: 500px !important;
        }
        
        /* Sticky Header for Chat Area Only */
        .main-header {
            position: sticky;
            top: 0;
            background-color: white;
            color: #EE1C25;
            padding: 1rem 0;
            z-index: 99;
            border-bottom: 2px solid #EE1C25;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
        }
        .header-title {
            font-size: 1.8rem;
            font-weight: 800;
            margin: 0;
            font-family: 'Inter', sans-serif;
        }

        .block-container {
            max-width: 800px;
            padding-top: 1rem !important; /* Reset padding since header is now in-flow */
            padding-bottom: 10rem;
        }
        /* Constrain chat input width and center it */
        [data-testid="stChatInput"] {
            max-width: 700px;
            margin-right: auto;
            margin-left: auto;
            left: 0;
            right: 0;
        }
        /* Coles theme accents */
        .stChatMessage [data-testid="stMarkdownContainer"] blockquote {
            border-left-color: #EE1C25;
        }
        .stChatInput button {
            color: #EE1C25 !important;
        }
        
        /* Sidebar Styling */
        .sidebar-greeting {
            font-size: 1.8rem;
            font-weight: 800;
            margin: 0;
            font-family: 'Inter', sans-serif;
            border-bottom: 1px solid #EE1C25;
            
            /* 1. Set the border-radius for rounded corners */
            border-radius: 25px; 
            
            /* 2. Set a transparent border. The width determines the border thickness. */
            border: 5px solid transparent; 

            /* 3. Apply the gradient as a background, clipped to the border area */
            background: linear-gradient(45deg, #EE1C25, #EE1C25) border-box;

            /* 4. Clip a solid white background (or your page background color) to the padding area, covering the inner part of the gradient */
            background-clip: padding-box, border-box; 
            
            /* Optional: Add padding for content spacing and center text */
            padding: 1.5rem;
            text-align: center;
        }

        
        
        /* Sidebar Suggestions Styling */
        [data-testid="stSidebar"] .stButton > button {
            border: 1px solid #EE1C25 !important;
            background-color: transparent !important;
            color: #EE1C25 !important;
            text-align: left !important;
            padding: 0.5rem 1rem !important;
            margin-bottom: 0.2rem !important;
            transition: all 0.2s ease !important;
            font-size: 0.9rem !important;
            line-height: 1.2 !important;
            width: 100% !important;
            border-radius: 8px !important;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: #EE1C25 !important;
            color: white !important;
            transform: translateX(5px);
        }
        /* Active suggestion style simulation */
        [data-testid="stSidebar"] .stButton > button:active {
            background-color: #b3141b !important;
            color: white !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

class SqlChatbot:

    def __init__(self):
        # We skip calling utils.sync_st_session() as it's causing crashes in this Streamlit version
        # and localize the LLM configuration to keep the sidebar clean.
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini", 
            temperature=0, 
            streaming=True, 
            api_key=st.secrets.get("OPENAI_API_KEY")
        )
    
    @st.cache_resource
    def get_db(_self, db_uri):
        if db_uri == 'USE_SAMPLE_DB':
            # Handle multi-page structure: page is in pages/, assets is in parent
            db_filepath = (Path(__file__).parent.parent / "assets/Chinook.db").absolute()
            db_uri = f"sqlite:////{db_filepath}"
            creator = lambda: sqlite3.connect(f"file:{db_filepath}?mode=ro", uri=True)
            db = SQLDatabase(create_engine("sqlite:///", creator=creator))
        else:
            db = SQLDatabase.from_uri(database_uri=db_uri)
        return db

    def get_agent(self, db):
        if "sql_agent" not in st.session_state:
            # Define visualization tool
            def visualize_data(input_str: str):
                """
                Creates a Plotly chart from SQL data.
                Input must be a string in the format: "chart_type|sql_query"
                Supported chart_types: 'bar', 'pie', 'line'
                Example: "pie|SELECT Name, Bytes FROM Track LIMIT 10"
                """
                try:
                    if "|" not in input_str:
                        return "Error: Input must be in 'chart_type|sql_query' format."
                    
                    chart_type, query = input_str.split("|", 1)
                    chart_type = chart_type.strip().lower()
                    query = query.strip()

                    df = pd.read_sql(query, db._engine)
                    if df.empty:
                        return "No data found for visualization."
                    
                    x_col = df.columns[0]
                    y_col = df.columns[1] if len(df.columns) > 1 else None
                    
                    if chart_type == "pie":
                        fig = px.pie(df, names=x_col, values=y_col if y_col else None, title="Data Distribution")
                    elif chart_type == "line":
                        fig = px.line(df, x=x_col, y=y_col, title="Trend Analysis")
                    else: # Default to bar
                        fig = px.bar(df, x=x_col, y=y_col, title="Comparison Chart")
                    
                    st.session_state["cur_fig"] = fig
                    st.plotly_chart(fig, use_container_width=True)
                    return f"Successfully rendered a {chart_type} chart."
                except Exception as e:
                    return f"Error: {str(e)}"

            visualize_tool = Tool(
                name="visualize_data",
                func=visualize_data,
                description="Use this to create charts. Input: 'chart_type|sql_query'. Types: bar, pie, line. Example: 'pie|SELECT Genre, Count(*) FROM Tracks GROUP BY Genre'"
            )

            memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
            st.session_state.sql_agent = create_sql_agent(
                llm=self.llm,
                db=db,
                extra_tools=[visualize_tool],
                top_k=10,
                verbose=False,
                agent_type="openai-tools",
                handle_parsing_errors=True,
                handle_sql_errors=True,
                memory=memory
            )
        return st.session_state.sql_agent

    def display_chat_ui(self):
        """Renders the header first, then the chat history to ensure correct ordering."""
        # 1. Render Header
        st.markdown(
            """
            <div class="main-header">
                <h1 class="header-title">🛒 MyThanks Chatbot</h1>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 2. Handle session state clearing (localized logic from utils)
        current_page = "SqlChatbot.main"
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = current_page
        if st.session_state["current_page"] != current_page:
            try:
                st.cache_resource.clear()
                del st.session_state["current_page"]
                del st.session_state["messages"]
            except:
                pass

        # 3. Display Chat History
        if "messages" not in st.session_state:
            st.session_state["messages"] = [{"role": "assistant", "content": "Please ask me anything about MyThanks!"}]
        
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if "fig" in msg:
                    st.plotly_chart(msg["fig"], use_container_width=True)

    def main(self):
        self.display_chat_ui()
        st.sidebar.markdown('<h1 class="sidebar-greeting" style="text-align: center; color: white;">Hello, User 👋</h1>', unsafe_allow_html=True)

        st.sidebar.divider()
        # Sidebar suggestions
        st.sidebar.markdown('<h3 style="text-align: center;">💡 Quick Suggestions</h3>', unsafe_allow_html=True)
        suggestions = [
            "Top 5 best-selling albums?",
            "Most popular music genres?",
            "Which artist has the most tracks?",
            "Summary of sales per country",
            "Trends in invoice totals"
        ]
        
        selected_suggestion = None
        for s in suggestions:
            # We use a trick to style these buttons specifically
            if st.sidebar.button(s, key=f"sug_{s}", use_container_width=True):
                selected_suggestion = s

        st.sidebar.divider()

        # Database Configuration (Hardcoded)
        db_uri = 'USE_SAMPLE_DB'
        db = self.get_db(db_uri)
        agent = self.get_agent(db)

        if st.sidebar.button("Back to Landing Page", use_container_width=True):
            st.switch_page("Home.py")

        user_query = st.chat_input(placeholder="Message MyThanks Chatbot...")
        
        # Override query if suggestion clicked
        if selected_suggestion:
            user_query = selected_suggestion

        if user_query:
            st.session_state.messages.append({"role": "user", "content": user_query})
            st.chat_message("user").write(user_query)

            with st.chat_message("assistant"):
                # Only show intermediate steps in Dev Mode
                is_dev_mode = st.secrets.get("GENERAL", {}).get("DEV_MODE", False)
                callbacks = []
                if is_dev_mode:
                    st_cb = StreamlitCallbackHandler(st.container())
                    callbacks.append(st_cb)
                
                result = agent.invoke(
                    {"input": user_query},
                    {"callbacks": callbacks}
                )
                response = result["output"]
                
                msg = {"role": "assistant", "content": response}
                if "cur_fig" in st.session_state:
                    msg["fig"] = st.session_state.pop("cur_fig")
                
                st.session_state.messages.append(msg)
                st.write(response)
                utils.print_qa(SqlChatbot, user_query, response)


if __name__ == "__main__":
    obj = SqlChatbot()
    obj.main()