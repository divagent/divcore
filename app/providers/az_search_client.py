# search_client.py
import os
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential

def get_search_client() -> SearchClient:
    """
    Returns an async Azure SearchClient instance
    """
    return SearchClient(
        endpoint="https://aisearch8.search.windows.net",
        index_name="aisearch8-div-index",
        credential=AzureKeyCredential(os.environ["AZURE_SEARCH_ADMIN_KEY"]),
    )
