from setuptools import setup, find_packages

setup(
    name="GrapheneGUI",
    version="0.1",
    description="A GTK-based graphical interface for creating and functionalizing graphene and graphene oxide sheets",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Nicolás Alfredo Loubet",
    author_email="nicolas.loubet@uns.edu.ar",
    url="https://github.com/nicolas-loubet/GrapheneGUI",  # Replace with your GitHub repo URL
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "PyGObject>=3.36.0",
        "numpy>=1.19.0",
    ],
    entry_points={
        "console_scripts": [
            "GrapheneGUI=GrapheneGUI.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.6",
)
