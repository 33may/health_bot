from langchain_huggingface import HuggingFaceEmbeddings

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={'device': 'mps'}
)

def compute_embedding(text):
    embedding = embedding_model.embed_query(text)
    return embedding


# sk-b7105f1a7cda46ab8b5410edfe6420f3