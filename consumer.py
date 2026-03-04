import logging
import json
from datetime import datetime
from quixstreams import Application
import psycopg2
from psycopg2 import sql
import os

# Load configuration from environment variables
POSTGRES_USER=os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD=os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB=os.getenv("POSTGRES_DB", "crypto_db")
POSTGRES_HOST=os.getenv("POSTGRES_HOST", "db")
POSTGRES_PORT=os.getenv("POSTGRES_PORT", "5432")
ASSET_LIST = [a.strip().upper() for a in os.getenv("ASSET_LIST", "btcusdt,ethusdt,solusdt").split(",")]
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "redpanda-0:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "crypto_prices")

def create_table_if_not_exists(conn):
    """
    Creates the crypto_prices table in postgres.
    """
    try:
        with conn.cursor() as cursor:
            columns = [sql.SQL("close_timestamp TIMESTAMP NOT NULL")]
            for asset in ASSET_LIST:
                columns.append(sql.Identifier(asset.lower()) + sql.SQL(" NUMERIC(18, 8)"))
            create_table_query = sql.SQL("CREATE TABLE IF NOT EXISTS crypto_prices ({})").format(
                sql.SQL(', ').join(columns)
            )
            cursor.execute(create_table_query)
            conn.commit()
            logging.info(f"Table ensured with assets: {ASSET_LIST}")
    except Exception as e:
        logging.error(f"Error creating table: {e}")
        conn.rollback()

def save_to_postgres(message, conn, aggregated):
    """
    Saves complete messages to a PostgreSQL database.
    """
    try:
        if all(message.get(asset) is not None for asset in ASSET_LIST):
            with conn.cursor() as cursor:
                cols = [sql.Identifier("close_timestamp")] + [sql.Identifier(a.lower()) for a in ASSET_LIST]
                placeholders = sql.SQL(", ").join([sql.Placeholder()] * len(cols))
                insert_query = sql.SQL("INSERT INTO crypto_prices ({}) VALUES ({})").format(
                    sql.SQL(", ").join(cols), placeholders
                )
                values = [message["close"]] + [message[asset] for asset in ASSET_LIST]
                cursor.execute(insert_query, values)
                conn.commit()
            timestamp = message["close"]
            if timestamp in aggregated:
                del aggregated[timestamp]              
            logging.info(f"Message saved to PostgreSQL: {message}")
    except Exception as e:
        conn.rollback()
        logging.error(f"Error saving to Postgres: {e}")

def transform_message(message, aggregated):
    """
    Transforms incoming messages and aggregates them by timestamp.
    """
    try:
        time = datetime.fromtimestamp(message['time'] / 1000).isoformat()
        ticker = message['ticker'].upper()
        if time not in aggregated:
            aggregated[time] = {asset: None for asset in ASSET_LIST}
            aggregated[time]["close"] = time
        if ticker in aggregated[time]:
            aggregated[time][ticker] = message['price'] 
        return aggregated[time]
    except KeyError as e:
        logging.error(f"Missing key in message: {e}")
        return None

def process_stream(app, input_topic, conn):
    """
    Processes the incoming data stream.
    """
    aggregated = {}
    sdf = app.dataframe(topic=input_topic)
    sdf = sdf.apply(lambda message: transform_message(message, aggregated))
    sdf = sdf.apply(lambda message: save_to_postgres(message, conn, aggregated))
    app.run(sdf)

def main():
    """
    Main entry point for the streaming application.
    """
    logging.info("START")

    # PostgreSQL connection setup
    conn = psycopg2.connect(
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
    )
    create_table_if_not_exists(conn)

    app = Application(
        broker_address=KAFKA_BROKER,
        consumer_group="postgres-consumer-group",
        auto_offset_reset="earliest",
    )

    # Quixstreams application setup
    input_topic = app.topic(name=KAFKA_TOPIC, value_deserializer="json")
    process_stream(app, input_topic, conn)

    conn.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    main()