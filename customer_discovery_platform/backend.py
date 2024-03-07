from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders.word_document import UnstructuredWordDocumentLoader
from langchain_community.document_loaders.markdown import UnstructuredMarkdownLoader
from langchain_community.document_loaders.powerpoint import UnstructuredPowerPointLoader
from langchain_community.document_loaders.email import OutlookMessageLoader
from langchain_community.document_loaders import UnstructuredEPubLoader
from langchain_community.document_loaders import GoogleDriveLoader
from langchain_community.document_loaders import UnstructuredFileIOLoader
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings


from langchain.prompts import PromptTemplate
from langchain_core.documents.base import Document
from langchain.chains.question_answering import load_qa_chain
from langchain_openai import OpenAI
from dotenv import load_dotenv

import os
import re
from flask import Flask, request, jsonify
from customer_discovery_platform.parsing import RefinedRegexParser

FILE_EXTENSIONS = {
    ".csv": (CSVLoader, {"encoding": "utf-8"}),
    ".doc": (UnstructuredWordDocumentLoader, {}),
    ".docx": (UnstructuredWordDocumentLoader, {}),
    ".md": (UnstructuredMarkdownLoader, {}),
    ".pdf": (PyPDFLoader, {}),
    ".ppt": (UnstructuredPowerPointLoader, {}),
    ".pptx": (UnstructuredPowerPointLoader, {}),
    ".txt": (TextLoader, {"encoding": "utf8"}), 
    ".msg" : (OutlookMessageLoader, {}), 
    'epub': (UnstructuredEPubLoader, {})
}

load_dotenv()

app = Flask(__name__)


def load_google_files(folder: str) -> list:
    """
    Read files from Google Drive.

    Parameters:
    -----------
        folder (str): the folder ID on Google Drive
    """
    docs = []
    doc_sheet_loader = GoogleDriveLoader(folder_id=folder,
                                         file_types=["document", "sheet"],
                                         file_loader_cls=UnstructuredFileIOLoader,
                                         recursive=True, 
                                         service_account_key=f'.credentials/key.json')

    slides_loader = GoogleDriveLoader(folder_id=folder,
                                      template="gdrive-mime-type",
                                      mime_type="application/vnd.google-apps.presentation",
                                      gslide_mode="slide", 
                                      recursive=True, 
                                      service_account_key=f'.credentials/key.json')
    
    for loader in [doc_sheet_loader, slides_loader]:
        for doc in loader.load():
            docs.append(doc.page_content)

    return docs


def make_db(path: str, google_path: str):
    """
    Read files from the lec_6_files/rag/docs directory and add them to a vector database.
    """
    #docs = [Document(doc) for doc in load_google_files(google_path)]
    docs = []

    for file in os.listdir(f'docs'):
        path, ext = os.path.join(f'docs', file), os.path.splitext(file)[1]
        if ext in FILE_EXTENSIONS:
            loader_class, loader_args = FILE_EXTENSIONS[ext]
            loader = loader_class(path, **loader_args)
            docs.extend(loader.load())

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = text_splitter.split_documents(docs)

    # On my setup load_dotenv was not finding my API key
    docembeddings = FAISS.from_documents(docs, OpenAIEmbeddings())
    docembeddings.save_local("llm_faiss_index")
    docembeddings = FAISS.load_local("llm_faiss_index",OpenAIEmbeddings())

    return docembeddings


def make_chain():
    """
    Make a chain to answer questions.
    """
    prompt_template = """Use the following pieces of context to answer the question at the end. 
    
    If you don't know the answer, just say that you don't know, don't try to make up an answer.

    This should be in the following format:

    Question: [question here]
    Helpful Answer: [answer here]
    Score: [score between 0 and 100]

    Begin!

    Context:
    ---------
    {context}
    ---------
    Question: {question}
    Helpful Answer:"""
    PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"],
        output_parser=RefinedRegexParser()
    )
    chain = load_qa_chain(OpenAI(temperature=0), chain_type="map_rerank", 
                          return_intermediate_steps=True, prompt=PROMPT)

    return chain


def get_answer(query, _docembeddings, _chain):
    """
    Get an answer to a question from an LLM while incorporating relevant documents.
    """
    relevant_chunks = _docembeddings.similarity_search_with_score(query, k=3)
    chunk_docs = []

    for chunk in relevant_chunks:
        chunk_docs.append(chunk[0])

    results = _chain({"input_documents": chunk_docs, "question": query})
    reference_text = ""

    for i in range(len(results["input_documents"])):
        reference_text += results["input_documents"][i].page_content

    output = {"Answer": results["output_text"][:results["output_text"].find(' Score: ')],
              "score": re.findall(r'Score:(.*)', results["output_text"])[-1],
              "Reference Document": results["input_documents"][i].metadata['source'], 
              "Reference Text": reference_text}
    
    return output
    

@app.route('/docqna', methods = ["POST"])
def processclaim():
    try:
        input_json = request.get_json(force=True)
        query, path = input_json["query"], input_json["path"]
        google_path = input_json["google_path"]
        embeddings, chain = make_db(path, google_path), make_chain()
        output = get_answer(query, embeddings, chain)
        return output
    except:
        return jsonify({"Status": "Failure --- some error occured"})
    
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8095, debug=True)
