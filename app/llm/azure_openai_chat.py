import os
from openai import AzureOpenAI, AsyncOpenAI

endpoint = "https://haystacked.cognitiveservices.azure.com/"
model_name = "gpt-5-nano"
deployment = "gpt-5-nano"

subscription_key = os.environ["AZURE_OPENAI_API_KEY"],
api_version = "2024-12-01-preview"

# client = AzureOpenAI(
#     api_version=api_version,
#     azure_endpoint=endpoint,
#     api_key=subscription_key,
# )

client = AsyncOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    base_url="https://haystacked.openai.azure.com/openai/v1/",
)


async def chat_completion_agent(system_prompt: str, user_prompt: str) -> str:
    resp = await client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return resp.choices[0].message.content



async def chat_completion_agent(messages: list) -> str:
    """
    Stateful reasoning unit for Agents. 
    Passes the full message history to maintain context/memory.
    """
    resp = await client.chat.completions.create(
        model=deployment,
        messages=messages,
        response_format={"type": "json_object"} # Forces JSON for easy parsing
    )
    return resp.choices[0].message.content


# async def chat_completion(system_prompt: str, user_prompt: str) -> str:
#     resp = await client.chat.completions.create(
#         model=model_name,
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_prompt},
#         ],
#         temperature=0.2,
#     )
#     return resp.choices[0].message.content


# response = client.chat.completions.create(
#     messages=[
#         {
#             "role": "system",
#             "content": "You are a helpful assistant.",
#         },
#         {
#             "role": "user",
#             "content": "I am going to Paris, what should I see?",
#         }
#     ],
#     max_completion_tokens=16384,
#     model=deployment
# )

# print(response.choices[0].message.content)


