from setuptools import setup, find_packages

setup(
    name="YA_MCPServer_YourTeam",
    version="0.1.0",
    description="YA MCP Server for YourTeam",
    packages=find_packages(exclude=["tests", "docs", "out"]),
    include_package_data=True,
)
