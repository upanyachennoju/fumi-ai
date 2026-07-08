from packages.providers.ollama import OllamaProvider


def get_llm_provider():
    return OllamaProvider()

    """
    if settings.provider == "ollama":
    return OllamaProvider()

    elif settings.provider == "lmstudio":
        return LMStudioProvider()
    
    """