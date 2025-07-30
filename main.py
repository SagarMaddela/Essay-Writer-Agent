# LOAD THE ENV CONTENT
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

# IMPORT THE REQUIRED LIBRARIES
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List, cast
import operator
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage
from langchain_groq import ChatGroq
from tavily import TavilyClient
import os
from pydantic import BaseModel
import streamlit as st

# IMPORTING THE MODEL and Agent
model = ChatGroq(model="llama-3.1-8b-instant",temperature=0.0)
tavily_tool = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# CREATING THE PROMPTS
PLAN_PROMPT = """You are an expert writer tasked with writing a high level outline of an essay. \
Write such an outline for the user provided topic. Give an outline of the essay along with any relevant notes \
or instructions for the sections."""

WRITER_PROMPT = """You are an essay assistant tasked with writing excellent 5-paragraph essays.\
Generate the best essay possible for the user's request and the initial outline. \
If the user provides critique, respond with a revised version of your previous attempts. \
Utilize all the information below as needed:

------

{content}"""

REFLECTION_PROMPT = """You are a teacher grading an essay submission. \
Generate critique and recommendations for the user's submission. \
Provide detailed recommendations, including requests for length, depth, style, etc."""

RESEARCH_PLAN_PROMPT = """You are a researcher charged with providing information that can \
be used when writing the following essay. Generate a list of 3 search queries that will gather \
any relevant information. **Only generate 3 queries max**"""

RESEARCH_CRITIQUE_PROMPT = """You are a researcher charged with providing information that can \
be used when making any requested revisions (as outlined below). \
Generate a list of search queries that will gather any relevant information. Only generate 3 queries max."""


# INITIALIZING MEMORY AND AGENT STATE
memory = MemorySaver()

class AgentState(TypedDict):
  task: str
  plan: str
  draft: str
  critique: str
  content: List[str]
  revision_number: int
  max_revisions: int

class Queries(BaseModel):
  queries: List[str]

# CREATING THE AGENT
class Agent:
  def __init__(self, model, tools, system=""):
    self.system = system
    graph = StateGraph(AgentState)

    def plan_action(state: AgentState):
        print("Executing plan action")
        messages = [
            SystemMessage(content=PLAN_PROMPT),
            HumanMessage(content=state['task'])
        ]
        response = model.invoke(messages)
        state['plan'] = response
        return {"plan": response.content}

    def research_plan_action(state: AgentState):
        print("Executing research plan action")
        queries = model.with_structured_output(Queries).invoke([
            SystemMessage(content=RESEARCH_PLAN_PROMPT),
            HumanMessage(content=state['plan'])
        ])
        content = state.get('content', [])
        for q in queries.queries:
            response = tavily_tool.search(query=q, max_results=1)
            print(f" Response =  {response}")
            for r in response['results']:
                content.append(r['content'])
        return {"content": content}

    def should_continue(state: AgentState):
        if state["revision_number"] > state["max_revisions"]:
            return END
        return "reflect"


    def generate_action(state: AgentState):
        print("Executing generate action")
        content = "\n\n".join(state.get('content', [])) 
        user_message = HumanMessage(
            content=f"{state['task']}\n\nHere is my plan:\n\n{state['plan']}")
        messages = [
            SystemMessage(
                content=WRITER_PROMPT.format(content=content)
            ),
            user_message
            ]
        response = model.invoke(messages)
        return {
            "draft": response.content,
            "revision_number": state.get("revision_number", 1) + 1
        }

    def reflect_action(state: AgentState):
        print("Executing reflect action")
        messages = [
        SystemMessage(content=REFLECTION_PROMPT),
        HumanMessage(content=state['draft'])
        ]
        response = model.invoke(messages)
        return {"critique": response.content}

    def research_critique_action(state: AgentState):
        print("Executing research critique action")
        queries = model.with_structured_output(Queries).invoke([
        SystemMessage(content=RESEARCH_CRITIQUE_PROMPT),
        HumanMessage(content=state['critique'])
        ])
        content = state.get('content', []) 
        for q in queries.queries:
            response = tavily_tool.search(query=q, max_results=2) 
            for r in response['results']: 
                content.append(r['content'])
        return {"content": content}


    graph.add_node("plan", plan_action)
    graph.add_node("research_plan", research_plan_action)
    graph.add_edge("plan", "research_plan")
    graph.add_node("generate", generate_action)
    graph.add_edge("research_plan", "generate")
    graph.add_node("reflect", reflect_action)
    graph.add_conditional_edges(
        "generate",
        should_continue,
        {END: END, "reflect": "reflect"}
    )
    graph.add_node("research_critique", research_critique_action)
    graph.add_edge("reflect", "research_critique")
    graph.add_edge("research_critique", "generate")
    graph.set_entry_point("plan")

    self.graph = graph.compile(checkpointer = memory)
    self.tools = [t.search for t in tools]
    self.model = model.bind_tools(self.tools)


# TESTING THE AGENT
user_prompt = """Generate an essay about solar system and its planets"""
abot = Agent(model,[tavily_tool],system = "user_prompt")

# STREAMLIT USER INTERFACE

def run_agent_live(user_prompt, max_revisions):
    abot = Agent(model, [tavily_tool], system="user_prompt")
    thread_id = "1"
    state = {
        'task': user_prompt,
        'plan': "",
        'draft': "",
        'critique': "",
        'content': [],
        'revision_number': 1,
        'max_revisions': max_revisions
    }
    state_typed = cast(AgentState, state)
    for step in abot.graph.stream(state_typed, config={"configurable": {"thread_id": thread_id}}, stream_mode="values"):
        yield step

def main():
    st.set_page_config(page_title="Essay Writer AI", layout="wide")
    st.title("📝 Essay Writer AI (Live Agent Steps)")
    st.markdown("Watch how the AI plans, researches, drafts, critiques, and improves your essay step-by-step.")

    with st.form("essay_form"):
        user_prompt = st.text_area("🎯 Essay Topic or Prompt", "Generate an essay about ...")
        max_revisions = st.number_input("🔁 Number of allowed revisions", min_value=1, max_value=5, value=2)
        submitted = st.form_submit_button("✍️ Generate Essay")

    if submitted:
        st.subheader("📡 Agent in Action")

        steps_display = st.empty()
        final_output_box = st.empty()
        progress_bar = st.progress(0.0)

        step_counter = 0
        total_steps = 2 + max_revisions * 3  # plan + research + N * (generate + reflect + research)
        steps_markdown = []

        with st.spinner("Generating your essay, please wait..."):
            for step in run_agent_live(user_prompt, max_revisions):
                step_counter += 1
                step_desc = ""

                # Add headings for each step
                if step.get("plan"):
                    step_desc += f"### 🧠 Plan\n{step['plan']}\n\n"
                if step.get("content"):
                    research_content = "\n\n".join(step['content']) if isinstance(step['content'], list) else str(step['content'])
                    step_desc += f"### 🔍 Research Content\n{research_content}\n\n"
                if step.get("draft"):
                    step_desc += f"### ✍️ Draft\n{step['draft']}\n\n"
                if step.get("critique"):
                    step_desc += f"### 🧪 Critique\n{step['critique']}\n\n"

                steps_markdown.append(step_desc)
                steps_display.markdown("\n---\n".join(steps_markdown), unsafe_allow_html=True)

                # Safe progress update
                progress = min(step_counter / total_steps, 1.0)
                progress_bar.progress(progress)

        # Show final output
        final_draft = step.get("draft", "No final draft generated.")
        final_critique = step.get("critique", "No critique available.")
        final_output_box.markdown(f"""
        ## ✅ Final Essay Output

        ### 📝 Essay:
        {final_draft}

        ### 🧑‍🏫 Final Critique:
        {final_critique}
        """, unsafe_allow_html=True)

        st.success("Essay generation complete!")


if __name__ == "__main__":
    main()
