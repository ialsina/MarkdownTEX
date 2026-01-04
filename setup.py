from setuptools import setup, find_packages

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name='Markdown-Toolkit',
    version='1.0.0',
    packages=find_packages("src"), # find_packages should search inside src
    package_dir={"": "src",},
    package_data={"mdtk": ["data/*.yaml", "data/*.txt", "data/*.json"]},
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mdtk=mdtk.tools.convert:mdtk",
            "mdtk-packages=mdtk.tools.package_help:md2tex_package_help",
            "mdtk-fonts=mdtk.tools.fonts:md2tex_supported_fonts",
        ]
    }
)