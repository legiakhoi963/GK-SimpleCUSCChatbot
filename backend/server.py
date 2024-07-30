import os
import pandas as pd
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain.retrievers import ContextualCompressionRetriever
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# EMBEDDINGS
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3"
)

# VECTOR STORE
qdrant = Qdrant.from_existing_collection(
    embeddings,
    path="database",
    collection_name="cusc",
)

# RETRIEVER
retriever = qdrant.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 10}
)

# CROSS ENCODER
cross_encoder = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-v2-m3")
compressor = CrossEncoderReranker(model=cross_encoder, top_n=4)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor, base_retriever=retriever
)

# API KEY
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

# LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

# SYSTEM PROMPT
system_prompt = (
    "Bạn là nhân viên tư vấn thông tin của trung tâm CUSC. "
    "Hãy sử dụng thông tin được cung cấp để trả lời câu hỏi. "
    "Nếu bạn không biết câu trả lời, hãy nói bạn không biết. "
    "Hãy trả lời ngắn gọn trong khoảng 5 câu. "
    "\n\n"
    "{context}"
)

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# CONTEXTUALIZE QUESTION
contextualize_q_system_prompt = (
    "Bằng cách sử dụng lịch sử cuộc trò chuyện và câu hỏi mới nhất của người dùng, "
    "hãy chỉnh sửa lại câu hỏi của người dùng để chứa thông tin có liên quan trong lịch sử cuộc trò chuyện nếu cần thiết. "
    "Không được phép trả lời câu hỏi của người dùng, "
    "chỉ chỉnh sửa lại câu hỏi của người dùng để chứa thông tin có liên quan trong lịch sử cuộc trò chuyện nếu cần thiết. "
)

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
history_aware_retriever = create_history_aware_retriever(llm, compression_retriever, contextualize_q_prompt)
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

# MANAGE CHAT HISTORY
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    store[session_id].messages = store[session_id].messages[-10:]
    return store[session_id]

# RAG CHAIN
conversational_rag_chain = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="answer",
)

# CLEAN RESPONSE
def clean_response(response: str) -> str:
    return response.replace("***", "").replace("**", "").replace("*","")

# FASTAPI
app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    session_id: str
    chat_request: str

class ChatResponse(BaseModel):
    chat_response: str

# Get user information
class UserInfo(BaseModel):
    name: str
    phone: str
    email: str
    address: str

# Store user information in a dictionary for demonstration
user_store = {}

router = APIRouter()

# CHAT API -> Using to catch "Chat" from Gemini API response
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        response = conversational_rag_chain.invoke(
            {"input": request.chat_request},
            config={"configurable": {"session_id": request.session_id}},
        )
        cleaned_response = clean_response(response["answer"])
        return ChatResponse(chat_response=cleaned_response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/user_info", response_model=UserInfo)
async def user_info_endpoint(user_info: UserInfo):
    try:
        # Store user information
        user_store[user_info.email] = user_info.dict()
        print("user_store", user_store)
        
        # Convert user information to DataFrame
        user_df = pd.DataFrame([user_info.dict()])
        print("user_df", user_df)

        # # Append DataFrame to Excel file without overwriting
        # with pd.ExcelWriter("user_info.xlsx", mode="a", engine="openpyxl") as writer:
        #     user_df.to_excel(writer, index=False, header=False, sheet_name="Sheet1", if_sheet_exists="replace")

        # CONCAT
        # Đọc dữ liệu hiện có từ tệp Excel vào DataFrame
        try:
            existing_df = pd.read_excel("user_info.xlsx", sheet_name="Sheet1")
        except FileNotFoundError:
            # Nếu tệp không tồn tại, tạo DataFrame mới
            existing_df = pd.DataFrame()

        # Nối dữ liệu mới với dữ liệu hiện có
        updated_df = pd.concat([existing_df, user_df], ignore_index=True)

        # Ghi DataFrame đã cập nhật vào tệp Excel
        updated_df.to_excel("user_info.xlsx", index=False, sheet_name="Sheet1")

        return user_info
    except Exception as e:
        # Log exception for debugging
        print(f"An error occurred: {e}")
        # Raise HTTPException with status code 500
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/sessions")
async def get_sessions():
    return list(store)  # Trả về danh sách tất cả các session_id đã được lưu trữ trong store

# Thêm router vào ứng dụng FastAPI
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
