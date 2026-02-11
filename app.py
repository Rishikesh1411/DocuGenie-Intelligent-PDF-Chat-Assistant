import asyncio
import nest_asyncio
import streamlit as st
import os
from dotenv import load_dotenv

# LangChain
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA

# ---- Fix for Streamlit + async ----
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
nest_asyncio.apply()
# -----------------------------------

# Load environment variables
load_dotenv()

# ✅ GROQ API KEY
groq_api_key = os.getenv("GROQ_API_KEY")

# Step 1: LLM (Groq)
llm = ChatGroq(
    model_name="llama-3.1-8b-instant",  # Free + Fast
    groq_api_key=groq_api_key,
    temperature=0.2
)

# Step 2: Local Embeddings (FREE)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Step 3: Streamlit UI
st.set_page_config(page_title="RAG with Groq", page_icon="🤖", layout="wide")
st.title("📂 RAG Q&A with Groq (FREE)")

uploaded_file = st.file_uploader("Upload a PDF, DOCX, or TXT file", type=["pdf", "txt", "docx"])

if uploaded_file:
    with st.spinner("Processing file... ⏳"):
        file_path = f"temp_{uploaded_file.name}"
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())

        # Load document
        if uploaded_file.name.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif uploaded_file.name.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
        else:
            loader = TextLoader(file_path)

        docs = loader.load()

        # Split text
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        chunks = splitter.split_documents(docs)

        # Vector store
        vectorstore = FAISS.from_documents(chunks, embeddings)
        retriever = vectorstore.as_retriever()

        # RAG chain
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            return_source_documents=True
        )

        st.success("✅ File processed successfully!")

        user_query = st.text_input("Ask a question from your file:")

        if st.button("Get Answer"):
            if user_query.strip() != "":
                with st.spinner("Generating answer... 🤔"):
                    response = qa.invoke({"query": user_query})

                    st.subheader("💡 Answer")
                    st.write(response["result"])

                    st.subheader("📎 Sources")
                    for i, doc in enumerate(response["source_documents"], 1):
                        st.markdown(f"**Source {i}:** {doc.metadata}")
                        st.write(doc.page_content[:200] + "...")
