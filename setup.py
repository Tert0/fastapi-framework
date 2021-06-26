from setuptools import setup, find_packages

with open("requirements.txt", "r") as file:
    requirements = [line.strip() for line in file.readlines()]

setup(
    name='fastapi-framework',
    packages=find_packages(),
    version='0.1.0',
    description='A Fastapi Framework',
    author='Tert0',
    license='MIT',
    install_requires=requirements
)
