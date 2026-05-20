# datalake_client.py
import os
from azure.storage.filedatalake import DataLakeServiceClient

def get_file_system_client():
    account_name = "hsstorageacc"
    account_key = os.getenv("HSSTORAGEACCKEY")
    container_name = "hsstoragecontainer"

    service_client = DataLakeServiceClient(
        account_url=f"https://{account_name}.dfs.core.windows.net",
        credential=account_key
    )

    file_system_client = service_client.get_file_system_client(container_name)
    return file_system_client
