from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant

# LOAD MULTIPLE TEXT FILES
loader = DirectoryLoader(
  "documents",
  glob="**/*.txt",
  loader_cls=TextLoader,
  loader_kwargs={"autodetect_encoding": True}
)
docs = loader.load()

# SPLIT TEXT FILES
text_splitter = RecursiveCharacterTextSplitter(
  chunk_size=1000,
  chunk_overlap=200
)
splits = text_splitter.split_documents(docs)

# EMBEDDINGS
embeddings = HuggingFaceEmbeddings(
  model_name="BAAI/bge-m3"
)

# VECTOR STORE
qdrant = Qdrant.from_documents(
  splits,
  embeddings,
  path="database",
  collection_name="cusc",
)

print("\033[1;32;40m DATA UPDATED SUCCESSFULLY! \033[0;0m")