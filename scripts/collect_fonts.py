"""Collect the available LaTeX fonts and font usages from
https://tug.org/FontCatalogue
"""

# pylint: disable=W0621

import json

from requests import Session
from bs4 import BeautifulSoup
from tqdm import tqdm

from mdtk.config import PATH_FONTS, PATH_FONT_USAGE

URL = "https://tug.org/FontCatalogue/"

class ResponseError(Exception):
    pass

def _get_soup(url: str, session: Session):
    response = session.get(url)
    if response.status_code != 200:
        raise ResponseError(response.status_code)
    return BeautifulSoup(response.text, "html.parser")

def get_font_usage(url: str, session: Session):
    """Given a font URL, return the font name and the LaTeX usage."""
    soup = _get_soup(url, session)
    h2_text = soup.find("h2").text
    for h3 in soup.find_all("h3"):
        if h3.text == "Usage":
            return h2_text, h3.next_sibling.next_sibling.text
    return h2_text, ""

def get_href_list(url: str, session: Session):
    """Given a URL, return a list of URLs listed within a <ul> tag.
    This can be used to get a list of category URLs in the main page,
    as well as to get a list of font URLSs in a category page
    """
    soup = _get_soup(url, session)
    pages = [URL + a.attrs["href"] for a in soup.find("ul").find_all("a")]
    return pages

def get_font_usages(session: Session):
    """Return a dictionary of font usages."""
    font_pages = []
    usages = {}
    category_pages = get_href_list(url=URL, session=session)
    for cat_page in tqdm(category_pages):
        font_pages.extend(get_href_list(url=cat_page, session=session))
    for font_page in tqdm(font_pages):
        name, usage = get_font_usage(url=font_page, session=session)
        # Skip font names with "special support" in the title, since they provoke redundancy
        if "special support" in name:
            continue
        usages.update({name: usage})
    return usages

if __name__ == "__main__":
    with Session() as session:
        font_usages = get_font_usages(session)
    with open(PATH_FONTS, "w", encoding="utf-8") as f:
        f.writelines("\n".join(sorted(font_usages.keys())))
    with open(PATH_FONT_USAGE, "w", encoding="utf-8") as f:
        f.write(json.dumps(font_usages))
