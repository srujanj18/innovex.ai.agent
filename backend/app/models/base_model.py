class BaseModel:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError