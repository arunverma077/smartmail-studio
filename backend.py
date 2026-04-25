import os
import time
from typing import TypedDict, List
from dotenv import load_dotenv
from email.message import EmailMessage
import smtplib

from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from langgraph.constants import START

# Gemini LLM
from langchain_google_genai import ChatGoogleGenerativeAI

# IMPORTANT: only import here (db.py must NOT import backend)
from db import save_email_to_history

load_dotenv()

# ---------------------------------------
# GRAPH STATE DEFINITION
# ---------------------------------------
class EmailState(TypedDict):
    request: str
    draft: str
    final_email: str
    recipients: List[str]
    subject: str
    from_addr: str
    username: str
    thread_id: str


# ---------------------------------------
# LLM INITIALIZATION (GEMINI)
# ---------------------------------------
llm = ChatGoogleGenerativeAI(
    model=os.getenv("LLM_MODEL", "gemini-3.1-flash-lite-preview"),
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.7
)


# ---------------------------------------
# HELPER: NORMALIZE GEMINI RESPONSE
# ---------------------------------------
def extract_text(response) -> str:
    """
    Normalize Gemini response into plain string.
    Handles:
    - list of chunks
    - dict with {type, text}
    - normal string
    """
    content = response.content

    # Case 1: list (chunks)
    if isinstance(content, list):
        texts = []
        for part in content:
            if isinstance(part, dict) and "text" in part:
                texts.append(part["text"])
            else:
                texts.append(getattr(part, "text", str(part)))
        return "".join(texts)

    # Case 2: dict
    if isinstance(content, dict):
        return content.get("text", str(content))

    # Case 3: string
    return str(content)


# ---------------------------------------
# NODE 1: GENERATE DRAFT
# ---------------------------------------
def generate_draft(state: EmailState):
    prompt = (
        "You are an expert AI email writer.\n"
        "Write a polished, professional email.\n\n"
        "STRICT RULES:\n"
        "- Return ONLY plain text\n"
        "- DO NOT return JSON or dict\n"
        "- First line must be: SUBJECT: <subject>\n\n"
        f"REQUEST:\n{state['request']}"
    )

    response = llm.invoke(prompt)

    # ✅ FIXED: Proper extraction
    response_text = extract_text(response).strip()

    subject = ""
    body = response_text

    # Extract subject safely
    if response_text.upper().startswith("SUBJECT:"):
        try:
            line1, rest = response_text.split("\n", 1)
            subject = line1.replace("SUBJECT:", "").strip()
            body = rest.strip()
        except Exception:
            pass

    return {
        "draft": body,
        "subject": subject
    }


# ---------------------------------------
# NODE 2: HUMAN REVIEW INTERRUPT
# ---------------------------------------
def human_review(state: EmailState):
    return interrupt({
        "task": "Review draft email",
        "draft_email": state.get("draft", ""),
        "subject": state.get("subject", "")
    })


# ---------------------------------------
# SMTP SENDER
# ---------------------------------------
def smtp_send(visible_from: str, to_addrs: List[str], subject: str, body: str):
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    use_tls = os.getenv("SMTP_TLS", "true").lower() in ("true", "1", "yes")

    if not all([host, smtp_user, smtp_pass]):
        raise RuntimeError("Missing SMTP credentials in .env")

    msg = EmailMessage()
    msg["From"] = visible_from
    msg["To"] = ", ".join(to_addrs)
    msg["Subject"] = subject or "(No Subject)"
    msg.set_content(body)

    server = smtplib.SMTP(host, port, timeout=30)
    try:
        server.ehlo()
        if use_tls:
            server.starttls()
            server.ehlo()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
    finally:
        server.quit()


# ---------------------------------------
# NODE 3: SEND EMAIL + SAVE HISTORY
# ---------------------------------------
def send_email(state: EmailState):
    recipients = state["recipients"]
    subject = state["subject"]
    body = state.get("final_email") or state.get("draft")

    smtp_user = os.getenv("SMTP_USER")
    sender_display_name = state["username"].strip().title()

    visible_from = f"{sender_display_name} <{smtp_user}>"

    # Send email
    smtp_send(visible_from, recipients, subject, body)

    # Save to history
    record = {
        "thread_id": state["thread_id"],
        "from_addr": visible_from,
        "to_addrs": ", ".join(recipients),
        "subject": subject,
        "body": body,
        "sent_at": int(time.time())
    }

    save_email_to_history(state["username"], record)

    return {"status": "sent", "record": record}


# ---------------------------------------
# LANGGRAPH PIPELINE
# ---------------------------------------
graph_builder = StateGraph(EmailState)

graph_builder.add_node("generate_draft", generate_draft)
graph_builder.add_node("human_review", human_review)
graph_builder.add_node("send_email", send_email)

graph_builder.add_edge(START, "generate_draft")
graph_builder.add_edge("generate_draft", "human_review")
graph_builder.add_edge("human_review", "send_email")

checkpointer = InMemorySaver()
graph = graph_builder.compile(checkpointer=checkpointer)


# ---------------------------------------
# PUBLIC API FUNCTIONS
# ---------------------------------------
def start_request(user_request: str, thread_id: str, username: str):
    config = {"configurable": {"thread_id": thread_id}}

    init_state = {
        "request": user_request,
        "username": username,
        "thread_id": thread_id,
    }

    return graph.invoke(init_state, config=config)


def resume_with_edit(
    edited_text: str,
    thread_id: str,
    recipients: list,
    subject: str,
    from_addr: str,
    username: str
):
    cmd = Command(resume={
        "final_email": edited_text,
        "recipients": recipients,
        "subject": subject,
        "from_addr": from_addr,
        "username": username,
        "thread_id": thread_id
    })

    config = {"configurable": {"thread_id": thread_id}}
    return graph.invoke(cmd, config=config)