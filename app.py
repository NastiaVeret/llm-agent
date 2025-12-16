import streamlit as st
import functions
from examiner_agent import ExaminerAgent
import json
from typing import Optional

st.set_page_config(page_title="AI Examiner Agent", page_icon="🎓")

st.markdown("""
<style>
    .stChatMessage {
        border-radius: 10px;
        padding: 10px;
    }
    .user-message {
        background-color: #f0f2f6;
    }
    .assistant-message {
        background-color: #e8f0fe;
    }
    h1 {
        color: #4B4B4B;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎓 AI Examiner Agent")
st.markdown("Welcome to the automated technical interview system. Please sign in to begin your assessment.")

with st.sidebar:
    st.header("Configuration")
    
    api_key_label = "Groq API Key"
    default_model = "llama-3.3-70b-versatile"

    api_key = st.text_input(api_key_label, type="password")
    
    if not api_key:
        st.warning(f"Please enter your Groq API Key to proceed.")

if "exam_started" not in st.session_state:
    st.session_state.exam_started = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "topics" not in st.session_state:
    st.session_state.topics = []
if "current_topic_index" not in st.session_state:
    st.session_state.current_topic_index = 0
if "exam_finished" not in st.session_state:
    st.session_state.exam_finished = False
if "final_score" not in st.session_state:
    st.session_state.final_score = None
if "final_feedback" not in st.session_state:
    st.session_state.final_feedback = ""

def reset_exam():
    st.session_state.exam_started = False
    st.session_state.messages = []
    st.session_state.topics = []
    st.session_state.current_topic_index = 0
    st.session_state.exam_finished = False
    st.session_state.final_score = None
    st.session_state.final_feedback = ""

if not st.session_state.exam_started and not st.session_state.exam_finished:
    with st.form("login_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email Address")
        submitted = st.form_submit_button("Start Exam")
        
        if submitted and api_key and name and email:
            topics = functions.start_exam(email, name)
            st.session_state.topics = topics
            st.session_state.user_info = {"name": name, "email": email}
            st.session_state.exam_started = True
            st.session_state.messages.append({"role": "assistant", "content": "Hello! I am your AI Examiner. I'm reviewing your profile..."})
            st.session_state.trigger_generation = True
            st.rerun()

if st.session_state.exam_started and not st.session_state.exam_finished:
    progress = st.session_state.current_topic_index / len(st.session_state.topics)
    st.progress(progress, text=f"Progress: {st.session_state.current_topic_index}/{len(st.session_state.topics)} Topics Completed")
    
    if st.session_state.current_topic_index < len(st.session_state.topics):
        current_topic = functions.get_next_topic(st.session_state.topics, st.session_state.current_topic_index)
        st.subheader(f"Current Topic: {current_topic}")
    else:
        st.subheader("Wrapping up...")

    for msg in st.session_state.messages:
        if msg.get("content"):
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
    def process_turn(user_input=None):
        agent = ExaminerAgent(api_key=api_key, model=default_model, base_url=base_url, temperature=0.3)
        
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                current_topic_name = functions.get_next_topic(st.session_state.topics, st.session_state.current_topic_index)
                if not current_topic_name:
                     current_topic_name = "Exam Review"
                
                remaining_topics = st.session_state.topics[st.session_state.current_topic_index+1:]
                
                response_msg = agent.generate_response(
                    st.session_state.messages, 
                    current_topic_name,
                    remaining_topics
                )
                
                if isinstance(response_msg, str): 
                   st.error(f"Error: {response_msg}")
                   return

                if response_msg.tool_calls:
                    msg_dict = {
                        "role": response_msg.role,
                        "content": response_msg.content,
                        "tool_calls": [t.model_dump() if hasattr(t, "model_dump") else t.dict() for t in response_msg.tool_calls]
                    }
                    st.session_state.messages.append(msg_dict)
                    
                    for tool_call in response_msg.tool_calls:
                        if tool_call.function.name == "transition_topic":
                            args = json.loads(tool_call.function.arguments)
                            score = args.get("topic_score")
                            reason = args.get("reasoning")
                            
                            if "scores" not in st.session_state:
                                st.session_state.scores = []
                            st.session_state.scores.append(score)
                            
                            st.session_state.current_topic_index += 1
                            
                            tool_output = {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": f"Topic concluded. Score: {score}. Reason: {reason}. Switching to next topic."
                            }
                            st.session_state.messages.append(tool_output)
                            
                            if st.session_state.current_topic_index >= len(st.session_state.topics):
                                pass 
                            
                        elif tool_call.function.name == "finish_exam":
                            args = json.loads(tool_call.function.arguments)
                            final_score = args.get("final_score")
                            feedback = args.get("feedback")
                            
                            st.session_state.final_score = final_score
                            st.session_state.final_feedback = feedback
                            st.session_state.exam_finished = True
                            
                            tool_output = {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": "Exam finished recorded."
                            }
                            st.session_state.messages.append(tool_output)
                            
                            functions.end_exam(
                                st.session_state.user_info['email'], 
                                final_score, 
                                st.session_state.messages
                            )
                            st.rerun()
                            return

                    process_turn(user_input=None)
    
                else:
                    st.write(response_msg.content)
                    msg_dict = {
                        "role": response_msg.role,
                        "content": response_msg.content
                    }
                    st.session_state.messages.append(msg_dict)


    if st.session_state.get("trigger_generation"):
        del st.session_state.trigger_generation
        process_turn()
    
    if prompt := st.chat_input("Type your answer here..."):
        process_turn(prompt)

if st.session_state.exam_finished:
    st.balloons()
    st.success(f"Exam Completed! Score: {st.session_state.final_score}/10")
    st.markdown("### Feedback")
    st.write(st.session_state.final_feedback)
    
    st.markdown("---")
    if st.button("Start New Exam"):
        reset_exam()
        st.rerun()
