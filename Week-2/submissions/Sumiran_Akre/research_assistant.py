from typing import List
import os
import imaplib
import arxiv
import requests
from io import BytesIO
from pypdf import PdfReader
import email as email_pkg
from datetime import datetime, timedelta
from email.header import decode_header
from email.utils import parsedate_to_datetime
from typing import Callable, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, field_validator
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage, BaseMessage


MAX_STEPS = 10
load_dotenv()
if not os.getenv("groq"):
    raise RuntimeError("GROQ_API_KEY is not set")
os.environ["GROQ_API_KEY"] = os.getenv("groq")

# email = os.getenv("email")
# app_pass = os.getenv("app_pass")

#INPUT VALIDATION, SCHEMA
class ArxivInput(BaseModel):
    topic: str = Field(..., description="Topic to search for")
    max_results: int = Field(default= 3, description="Maximum number of results")

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v):
        if not v.strip():
            raise ValueError("Topic cannot be empty")
        return v

    @field_validator("max_results")
    @classmethod
    def validate_results(cls, v):
        if not 1 <= v <= 5:
            raise ValueError("max_results must be between 1 and 5")
        return v

class PDFInput(BaseModel):
    pdf_path: str = Field(..., description="Path to the PDF file")

    @field_validator("pdf_path")
    @classmethod
    def validate_pdf_path(cls, v):
        if not v.endswith(".pdf"):
            raise ValueError("Invalid PDF path")
        return v

class EmailInput(BaseModel):
    email: str = Field(..., description="Email address")
    app_pass: str = Field(..., description="App password")
    days: int = Field(default= 1, description="Number of days")
    imap_server: str = Field(default = "imap.gmail.com", description="IMAP server")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email")
        return v

    @field_validator("app_pass")
    @classmethod
    def validate_pass(cls, v):
        if len(v) != 16:
            raise ValueError("App password must be 16 characters")
        return v

    @field_validator("days")
    @classmethod
    def validate_days(cls, v):
        if not 1 <= v <= 10:
            raise ValueError("Days must be between 1 and 10")
        return v

#TOOLS FUNCTION DEFINITIONS
def search_arxiv(topic: str, max_results: int) -> str:
    try:
        client = arxiv.Client(
            delay_seconds=3,
            num_retries=5,
            page_size=max_results
        )

        search = arxiv.Search(
            query=topic,
            max_results=max_results
        )

        results = []

        for paper in client.results(search):
            results.append(
                f"Title: {paper.title}\n"
                f"Authors: {', '.join(a.name for a in paper.authors)}\n"
                f"PDF: {paper.pdf_url}\n"
            )

        return "\n\n".join(results)

    except Exception as e:
        return f"Arxiv Error: {e}"

def summarize_pdf(pdf_path: str):
    if pdf_path.startswith('http'):
        response = requests.get(pdf_path, timeout=20)
        pdf_file = BytesIO(response.content)
        reader = PdfReader(pdf_file)
        
    else:
        return "Only online links supported"
    text = ""
    for page in reader.pages:
        text += page.extract_text()

    response = llm.invoke(
            f""" Summarize this PDF content in concise bullet points with academic tone in format :
            <Title>, <Authors>, <Summary>, <Requirements>, <Insights> and <Conclusion>
            {text}
            """
        )
    return response.content

def process_last_x_emails(email: str, app_pass: str, days: int, imap_server: str) -> str:

    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email, app_pass)
        mail.select("inbox")

        since = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")

        status, messages = mail.search(None,f'(SINCE "{since}")')
        if status != 'OK':
            return "Error searching for emails."
        
        ids = messages[0].split()

        if not ids:
            return "No emails found."

        output = []

        for idx, mail_id in enumerate(ids):
            _, msg_data = mail.fetch(mail_id, "(RFC822)")
            for part in msg_data:
                if not isinstance(part, tuple):
                    continue
                msg = email_pkg.message_from_bytes(part[1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8",errors="ignore")
                sender = msg.get("From")
                date_header = msg.get("Date")
                if date_header:
                    dt = parsedate_to_datetime(date_header).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    dt = "Unknown"

                output.append(
                    f"Message {idx+1}\n"
                    f"Time: {dt}\n"
                    f"Sender: {sender}\n"
                    f"Subject: {subject}\n"
                )

        mail.close()
        mail.logout()

        return "\n\n".join(output)

    except Exception as e:
        return f"Email Error: {e}"

# TOOL WRAPPER
class Tool:

    def __init__(self, name: str, description: str, input_model: type[BaseModel],func: Callable[..., str]):
        self.name = name
        self.description = description
        self.input_model = input_model
        self.func = func

    def run(self, raw_input: dict[str, Any]) -> str:

        try:
            validated = self.input_model(**raw_input)
            return self.func(**validated.model_dump())
        except ValidationError as e:
            return f"Validation Error:\n{e}"
        except Exception as e:
            return f"Tool Error: {e}"

    def to_groq_tool(self):

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": (
                    self.input_model
                    .model_json_schema()
                ),
            },
        }

#TOOL REGISTRY
TOOLS = [
    Tool(
        "search_arxiv",
        "Search research papers on arxiv",
        ArxivInput,
        search_arxiv,
    ),
    Tool(
        "summarize_pdf",
        "Summarize the contents of a PDF file.",
        PDFInput,
        summarize_pdf,
    ),
    Tool(
        "process_last_x_emails",
        "Process recent emails",
        EmailInput,
        process_last_x_emails,
    ),
]

TOOL_MAP = {tool.name: tool for tool in TOOLS}

#MODEL INITIALIZATION
llm = ChatGroq(
    model_name="llama-3.3-70b-versatile"
)

llm_with_tools = llm.bind_tools([tool.to_groq_tool() for tool in TOOLS])

#AGENT DEFINITIONS
class ResearchAgent:

    def __init__(self, history: List[BaseMessage]):
        self.messages = history

    def run( self, query: str) -> str:
        self.messages.append(HumanMessage(content=query))

        for _ in range(MAX_STEPS):
            response = llm_with_tools.invoke(self.messages)
            self.messages.append(response)

            if not response.tool_calls:
                return str(response.content), self.messages

            for tool_called in response.tool_calls:
                tool_name = tool_called["name"]
                tool_args = tool_called["args"]
                print(f"\n[TOOL]: {tool_name}")
                print(f"[ARGS]: {tool_args}")
                tool = TOOL_MAP.get(tool_name)
                if not tool:
                    result = (f"Unknown Tool: " f"{tool_name}")
                else:
                    result = tool.run(tool_args)
                print(f"[TOOL OUTPUT]: {result}")
                self.messages.append(ToolMessage(content=result,tool_call_id=tool_called["id"]))

        return (
            "Stopped after reaching "
            "MAX_STEPS."
        ), self.messages


if __name__ == "__main__":

    print("\n[AGENT] Hello! How can I help you today?\n")

    chat_history = [
        SystemMessage(content = '''You are a helpful assistant. You have access to three tools if you need them. 
        But you should reveal about your tool used, provide me with onlya detailed output.
        The 3 tools are -: 
        1.  search_arxiv: Searches for research papers on arXiv (args: topic: str, max_results: int)
        2.  summarize_pdf: Summarizes the contents of a PDF file as descriptin in the tool (args: pdf_path: str)
        3.  process_last_x_emails: Processes last x emails (args: email: str, app_pass: str, days: int, imap_server: str)

        When using the tool 1, try to provide an output in bulleted list format, containing title, authors, small 2-3 line summary and pdf link.
        When using the tool 2, try to provide an output same as given by tool but with some beauty added to it.
        When using the tool 3, try to provide an output as markdown with header as Message Number containing time, sender and subject.
        Don't reveal about your tool used, provide me with only a detailed output.
        
        '''),
    ]

    agent = ResearchAgent(chat_history)

    while True:

        query = input("[You] ").strip()

        if query.lower() in ["exit","quit","bye"]:
            break

        answer, chat_history = agent.run(query)
        print(f"\n[Agent] : {answer}\n")
