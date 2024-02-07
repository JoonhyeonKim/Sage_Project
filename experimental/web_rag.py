from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain.chains import create_retrieval_chain
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import HTMLHeaderTextSplitter
from langchain_experimental.text_splitter import SemanticChunker

llm = ChatGoogleGenerativeAI(model="gemini-pro")

# loader = WebBaseLoader("https://en.wikipedia.org/wiki/Franken_Fran")
# loader = WebBaseLoader("https://tvtropes.org/pmwiki/pmwiki.php/Characters/FrankenFran")

# Loading multiple webpages
loader = WebBaseLoader(["https://bitvijays.github.io/Series_Vulnerable_Machines/LFC-VM-P0-InitialRecon.html", 
                        "https://bitvijays.github.io/Series_Vulnerable_Machines/LFC-VM-P1-FromNothingToUnprivilegedShell.html",
                        "https://bitvijays.github.io/Series_Vulnerable_Machines/LFC-VM-P2-UnprivilegedToPrivilegedShell.html",
                        "https://bitvijays.github.io/Series_Vulnerable_Machines/LFC-VM-P3-TipsAndTricks.html",
                        "https://bitvijays.github.io/Series_Vulnerable_Machines/LFC-VM-P4-Appendix.html",
                        "https://bitvijays.github.io/Series_Capture_The_Flag/LFC-BinaryExploitation.html",
                        "https://bitvijays.github.io/Series_Capture_The_Flag/LFC-Forensics.html",
                        "https://bitvijays.github.io/Series_Capture_The_Flag/LFC-ReverseEngineering.html",
                        "https://bitvijays.github.io/Series_Capture_The_Flag/LFC-Cryptography.html",
                        "https://bitvijays.github.io/Series_Capture_The_Flag/LFC-CodingQuickRef.html",
                        "https://bitvijays.github.io/Series_Critical_Infrastructure/LFF-CIS-ElectricalGrid.html",
                        "https://bitvijays.github.io/Series_The_Essentials/LFF-ESS-P0A-CyberSecurityEnterprise.html",
                        "https://bitvijays.github.io/Series_The_Essentials/LFF-ESS-P0B-LinuxEssentials.html",
                        "https://bitvijays.github.io/Series_The_Essentials/LFF-ESS-P0C-CloudEssentials.html",
                        "https://bitvijays.github.io/Series_The_Essentials/LFF-ESS-P0E-OpenSource.html",
                        "https://bitvijays.github.io/Series_The_Essentials/LFF-ESS-P0D-SecureSoftware.html",
                        "https://bitvijays.github.io/Series_The_Essentials/LFF-ESS-P0F-IndustrialControlSystems.html",
                        "https://bitvijays.github.io/Series_Infrastructure_Pentest/LFF-IPS-P1-IntelligenceGathering.html",
                        "https://bitvijays.github.io/Series_Infrastructure_Pentest/LFF-IPS-P2-VulnerabilityAnalysis.html",
                        "https://bitvijays.github.io/Series_Infrastructure_Pentest/LFF-IPS-P3-Exploitation.html",
                        "https://bitvijays.github.io/Series_Infrastructure_Pentest/LFF-IPS-P4-PostExploitation.html",
                        "https://bitvijays.github.io/Series_Infrastructure_Pentest/LFF-IPS-P5-Reporting.html",
                        "https://bitvijays.github.io/Series_Infrastructure_Pentest/LFF-IPS-P6-ConfigurationReview.html",])

# all_docs = []
# for url in url_list:
#     loader = WebBaseLoader([url])
#     docs = loader.load()
#     all_docs.extend(docs) 

# # loader.requests_kwargs = {'verify':False}
docs = loader.load()
# print(docs[0])
# print(docs)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
# db = FAISS.from_documents(docs, embeddings)
# db.save_local("faiss_index")

headers_to_split_on = [
    ("h1", "Header 1"),
    ("h2", "Header 2"),
    ("h3", "Header 3"),
]

# html_splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
# html_header_splits = html_splitter.split_text_from_url(url)
# doc = html_splitter.split_text(docs[0])

# text_splitter = SemanticChunker(embeddings)

# print(doc)
chunk_size = 200
chunk_overlap = 30
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=chunk_size, chunk_overlap=chunk_overlap
)
documents = text_splitter.split_documents(docs)
# print(documents)
vector = FAISS.from_documents(documents, embeddings)

print(vector)
vector.save_local("faiss_cyse")

# new_vector = FAISS.load_local("faiss_cyse", embeddings)

# prompt = ChatPromptTemplate.from_template("""Answer the following question based only on the provided context:

# <context>
# {context}
# </context>

# Question: {input}""")

# document_chain = create_stuff_documents_chain(llm, prompt)
# retriever = vector.as_retriever()
# # retriever = new_vector.as_retriever()
# retrieval_chain = create_retrieval_chain(retriever, document_chain)

# response = retrieval_chain.invoke({"input": "What is usually on port 21?"})
# print(response["answer"])


# document_chain.invoke({
#     "input": "how can langsmith help with testing?",
#     "context": [Document(page_content="langsmith can let you visualize test results")]
# })

# prompt = ChatPromptTemplate.from_messages([
#     ("system", "You are world class technical documentation writer."),
#     ("user", "{input}")
# ])
# output_parser = StrOutputParser()
# chain = prompt | llm | output_parser
# a = chain.invoke({"input": "how can langsmith help with testing?"})
# print(a, type(a))