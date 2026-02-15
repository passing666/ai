from resources import YA_MCPServer_Resource
from typing import Any
import json


@YA_MCPServer_Resource(
    "file:///resources/sample_data.json",
    name="sample_data",
    title="Sample Data Resource",
    description="返回示例数据集（JSON）",
)
def get_sample_data() -> Any:
    try:
        with open("resources/sample_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "sample_data.json not found"}
