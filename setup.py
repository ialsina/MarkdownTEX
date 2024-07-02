from setuptools import setup, find_packages

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name='MarkdownTEX',
    version='1.0.0',
    packages=find_packages(),
    package_dir={"": "src",},
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mdtk=mdtex.tools.convert:mdtk",
            "mdtk-packages=mdtex.tools.package_help:md2tex_package_help",
            "mdtk-fonts=mdtex.tools.fonts:md2tex_supported_fonts",
        ]
    }
)