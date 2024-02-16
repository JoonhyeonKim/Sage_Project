from langchain_core.output_parsers import StrOutputParser
from langchain_experimental.llm_bash.bash import BashProcess
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


def sanitize_output(text: str):
    _, after = text.split("```bash")
    return after.split("```")[0]


template = """Write some bash code to solve the user's problem. 

Return only bash code in Markdown format, e.g.:

```bash
....
```"""
prompt = ChatPromptTemplate.from_messages([("system", template), ("human", "{input}")])

model = ChatOpenAI()

chain = prompt | model | StrOutputParser() | sanitize_output | BashProcess().run

print(chain.invoke({"input": "I wanna find the file that is changed 12 days ago"}))
print(BashProcess())