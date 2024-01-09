import re
import html
import streamlit as st
from requests import get

BASE_URL = "https://hacker-news.firebaseio.com/v0/item/"
CLEANR = re.compile('<.*?>')


def get_comment_ids(story: int) -> list:
    story_info = get(BASE_URL + f"{story}.json", timeout=30).json()
    comment_ids = story_info.get("kids")
    return comment_ids


def format_html(text_string: str):
    unescaped_text = html.unescape(text_string)
    clean_text = re.sub(CLEANR, '', unescaped_text)
    return clean_text


def get_top_5_most_replied_parent_comments(story_id: int):
    parent_comments = get_comment_ids(story_id)

    parent_comments_list = []
    for parent_comment_id in parent_comments:
        comment_info = get(
            BASE_URL + f"{parent_comment_id}.json", timeout=30).json()
        comment_text = comment_info.get("text")
        comment_title = format_html(
            comment_text[:60]) if comment_text else "No title available"
        number_of_children = 0
        kids_info = comment_info.get("kids")
        if kids_info is not None:
            number_of_children = len(kids_info)

        parent_comments_list.append(
            {'title': comment_title, 'number_of_children': number_of_children})

    sorted_list = sorted(parent_comments_list, key=lambda comment_dict: comment_dict.get(
        'number_of_children', 0), reverse=True)
    return sorted_list[:5]


def cycle_text(text_list, interval=2):
    index = 0
    placeholder = st.empty()

    while True:
        placeholder.text(text_list[index])
        index = (index + 1) % len(text_list)
        st.experimental_rerun()
        st.sleep(interval)


if __name__ == "__main__":
    st.title("Cycling Text Box")

    top_5_comments = get_top_5_most_replied_parent_comments(38865518)
    text_list = [
        f"{parent_comment.get('title')} - - - [{parent_comment.get('number_of_children')} replies]" for parent_comment in top_5_comments
    ]

    cycle_text(text_list)
