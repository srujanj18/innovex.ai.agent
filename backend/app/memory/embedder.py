from sentence_transformers import SentenceTransformer

hf_model = None


def get_embedding_model():
    global hf_model

    if hf_model is not None:
        return hf_model

    try:
        hf_model = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as e:
        print(f"HF embedding model unavailable: {e}")
        hf_model = False

    return hf_model


def get_embedding(text: str):
    try:
        model = get_embedding_model()
        if not model:
            return [0.0] * 384

        return model.encode(text).tolist()
    except Exception as e:
        print(f"HF embedding failed: {e}")
        return [0.0] * 384
