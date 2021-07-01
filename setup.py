from setuptools import setup, find_packages

with open("requirements.txt", "r") as file:
    requirements = [line.strip() for line in file.readlines()]

with open("README.md", "r") as file:
    readme = file.read().replace("[ ]", "❌").replace("[x]", "✅")

setup(
    name="fastapi-framework",
    packages=find_packages(),
    version="1.0.0",
    description="A Fastapi Framework",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Tert0",
    license="MIT",
    install_requires=requirements,
    extra_requires=["mkdocs-material", "black", "coverage"],
    url="https://github.com/Tert0/fastapi-framework",
    python_requires=">=3.6",
)
