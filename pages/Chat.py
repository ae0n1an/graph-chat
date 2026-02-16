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

st.set_page_config(page_title="MyThanks Chatbot", page_icon="🛒", layout="wide")
st.title('MyThanks Chatbot')

class SqlChatbot:

    def __init__(self):
        utils.sync_st_session()
        self.llm = utils.configure_llm()
    
    @st.cache_resource
    def get_db(_self, db_uri):
        if db_uri == 'USE_SAMPLE_DB':
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

    @utils.enable_chat_history
    def main(self):

        # User inputs
        radio_opt = ['Use sample db','Connect to your SQL db']
        selected_opt = st.sidebar.radio(
            label='Choose suitable option',
            options=radio_opt
        )
        if radio_opt.index(selected_opt) == 1:
            with st.sidebar.popover(':orange[⚠️ Security note]', use_container_width=True):
                warning = "Building Q&A systems of SQL databases requires executing model-generated SQL queries. There are inherent risks in doing this. Make sure that your database connection permissions are always scoped as narrowly as possible for your chain/agent's needs.\n\nFor more on general security best practices - [read this](https://python.langchain.com/docs/security)."
                st.warning(warning)
            db_uri = st.sidebar.text_input(
                label='Database URI',
                placeholder='mysql://user:pass@hostname:port/db'
            )
        else:
            db_uri = 'USE_SAMPLE_DB'
        
        if not db_uri:
            st.error("Please enter database URI to continue!")
            st.stop()
        
        db = self.get_db(db_uri)
        agent = self.get_agent(db)

        with st.sidebar.expander('Database tables', expanded=True):
            st.info('\n- '+'\n- '.join(db.get_usable_table_names()))

        user_query = st.chat_input(placeholder="Message MyThanks Chatbot...")

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