# ser_data_lake.py
import json
from datetime import datetime
from app.core.azure_data_lake import get_file_system_client  # your existing module

fs_client = get_file_system_client()  # reuse client

def write_json(payload: dict, folder: str = "test_files") -> str:
    file_name = f"{folder}/{datetime.utcnow().strftime('%Y-%m-%d-%H%M%S')}.json"
    file_client = fs_client.get_file_client(file_name)

    content = json.dumps(payload)
    file_client.create_file()
    file_client.append_data(content.encode('utf-8'), 0, len(content))
    file_client.flush_data(len(content))
    return file_name

# def list_files(folder: str = "") -> list[str]:
#     return [path.name for path in fs_client.get_paths(path=folder)]

def list_files() -> list[str]:
    paths = fs_client.get_paths("")
    return [p.name for p in paths]