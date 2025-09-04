from setuptools import setup, find_packages

setup(
    name="GrapheneGUI",
    version="2.2",
    description="Qt-based graphical interface for creating and functionalizing graphene and graphene oxide plates",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Nicolás Alfredo Loubet",
    author_email="nicolas.loubet@uns.edu.ar",
    url="https://github.com/nicolas-loubet/GrapheneGUI",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "graphenegui": [
            "ui/*.ui",
            "ui/*.py",
            "ui/img/png/*.png",
            "ui/img/svg/*.svg",
            "ui/resources.qrc",
            "ui/resources_rc.py",
        ],
    },
    install_requires=[
        "PySide6>=6.0.0",
        "numpy>=1.19.0",
    ],
    entry_points={
        "console_scripts": [
            "graphene-gui=graphenegui.__main__:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.6",
)
