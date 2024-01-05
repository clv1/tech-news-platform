'''Sends SMS if viral article detected. '''
from os import environ
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL
import pandas as pd
import boto3

load_dotenv()

THRESHOLD = 20
STORY_LIMIT = 200

engine_url_object = URL.create(
        "postgresql+psycopg2",
        username=environ['DB_USER'],
        password=environ['DB_PASSWORD'],
        host=environ['DB_HOST'],
        database=environ['DB_NAME'],
        )


def viral_checker(threshold: int, story_limit: int) -> list[dict]:
    """Returns a list of dictionaries with each story above the score threshold."""
    # look into being able to return a %growth
    viral_query = f"""
        WITH LatestTwoRecords AS (
        SELECT
            story_id,
            score,
            ROW_NUMBER() OVER (PARTITION BY story_id ORDER BY record_time DESC) AS row_num
        FROM
            records
        )
        SELECT
            story_id
        FROM
            LatestTwoRecords
        WHERE
            row_num <= 2
            AND story_id IN (SELECT story_id FROM records ORDER BY record_id DESC LIMIT {story_limit})
        GROUP BY
            story_id
        HAVING
            COALESCE(MAX(CASE WHEN row_num = 1 THEN score END) - MAX(CASE WHEN row_num = 2 THEN score END), 0) > {threshold};
        """
    engine = create_engine(engine_url_object)

    story_info = []
    story_ids = tuple(pd.read_sql(viral_query, engine)["story_id"].to_list())
    if story_ids:
        story_info_query = f"""SELECT title, story_url FROM stories WHERE story_id IN {story_ids};"""
        story_info = pd.read_sql(story_info_query, engine).to_dict(orient="records")
        
    return story_info


def generate_viral_notif_msg(stories: list) -> str:
    """Creates a SMS message with details about viral stories."""
    msg = """🚨VIRAL STORY🚨"""
    for story in stories:
        msg += f"\n • {story.get('title')} ({story.get('story_url')})"
    msg += "\nMake sure to check them out."
    return msg


def lambda_handler(event, context):
    """This function sends an SMS if a story has reached a certain amount of likes per hour."""
    viral_stories = viral_checker(THRESHOLD, STORY_LIMIT)
    if viral_stories:
        try:
            client = boto3.client('sns')
            response = client.publish(TopicArn='arn:aws:sns:eu-west-2:129033205317:c9-tech-news-sms',
                                    Message=generate_viral_notif_msg(viral_stories))
            return response
        except Exception as e:
            return f"Error sending SMS: {e}"
    return "No viral stories found."


if __name__ == "__main__":

    lambda_handler("h","g")
