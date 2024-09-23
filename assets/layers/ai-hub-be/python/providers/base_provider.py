from abc import ABC, abstractmethod
from langchain.llms.base import LLM

class BaseProvider(ABC):
    """
    Abstract base class for AI model providers.
    All provider-specific classes must inherit from this class and implement the get_llm method.
    """

    @abstractmethod
    def get_llm(self) -> LLM:
        """
        Instantiate and return the LangChain LLM class specific to the provider.
        
        Returns:
            LLM: An instance of a LangChain LLM.
        """
        pass
