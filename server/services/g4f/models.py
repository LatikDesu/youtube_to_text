import random

from server.services.g4f import Provider


class Model:
    class model:
        name: str
        base_provider: str
        best_provider: str

    class gpt_35_turbo:
        name: str = 'gpt-3.5-turbo'
        base_provider: str = 'openai'
        best_provider: Provider.Provider = random.choice([Provider.DeepAi, Provider.Easychat])

    class gpt_35_turbo_0613:
        name: str = 'gpt-3.5-turbo-0613'
        base_provider: str = 'openai'
        best_provider: Provider.Provider = random.choice([Provider.Easychat])

    class gpt_35_turbo_16k_0613:
        name: str = 'gpt-3.5-turbo-16k-0613'
        base_provider: str = 'openai'
        best_provider: Provider.Provider = random.choice([Provider.Easychat])

    class gpt_35_turbo_16k:
        name: str = 'gpt-3.5-turbo-16k'
        base_provider: str = 'openai'
        best_provider: Provider.Provider = random.choice([Provider.Easychat])

    class gpt_4_dev:
        name: str = 'gpt-4-for-dev'
        base_provider: str = 'openai'
        best_provider: Provider.Provider = Provider.Phind

    class gpt_4:
        name: str = 'gpt-4'
        base_provider: str = 'openai'
        best_provider: Provider.Provider = Provider.Lockchat
        best_providers: list = [Provider.Bing, Provider.Lockchat]

    class gpt_4_0613:
        name: str = 'gpt-4-0613'
        base_provider: str = 'openai'
        best_provider: Provider.Provider = Provider.Lockchat
        best_providers: list = [Provider.Bing, Provider.Lockchat]

    class palm:
        name: str = 'palm2'
        base_provider: str = 'google'
        best_provider: Provider.Provider = Provider.Bard

    """    'falcon-40b': Model.falcon_40b,
    'falcon-7b': Model.falcon_7b,
    'llama-13b': Model.llama_13b,"""

    class falcon_40b:
        name: str = 'falcon-40b'
        base_provider: str = 'huggingface'
        best_provider: Provider.Provider = Provider.H2o

    class falcon_7b:
        name: str = 'falcon-7b'
        base_provider: str = 'huggingface'
        best_provider: Provider.Provider = Provider.H2o

    class llama_13b:
        name: str = 'llama-13b'
        base_provider: str = 'huggingface'
        best_provider: Provider.Provider = Provider.H2o


class ModelUtils:
    convert: dict = {
        'gpt-3.5-turbo': Model.gpt_35_turbo,
        'gpt-3.5-turbo-0613': Model.gpt_35_turbo_0613,
        'gpt-4': Model.gpt_4,
        'gpt-4-0613': Model.gpt_4_0613,
        'gpt-4-for-dev': Model.gpt_4_dev,
        'gpt-3.5-turbo-16k': Model.gpt_35_turbo_16k,
        'gpt-3.5-turbo-16k-0613': Model.gpt_35_turbo_16k_0613,

        'palm2': Model.palm,
        'palm': Model.palm,
        'google': Model.palm,
        'google-bard': Model.palm,
        'google-palm': Model.palm,
        'bard': Model.palm,

        'falcon-40b': Model.falcon_40b,
        'falcon-7b': Model.falcon_7b,
        'llama-13b': Model.llama_13b,
    }
