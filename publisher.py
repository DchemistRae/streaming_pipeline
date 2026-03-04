import websocket
import json
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError
import os

# Load configuration from environment variables
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "redpanda-0:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "crypto_prices") 
ASSET_LIST = os.getenv("ASSET_LIST", "btcusdt,ethusdt,solusdt").split(",")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL", "wss://stream.binance.com:9443/ws")

def send_data_to_kafka(data_dict, producer):
    """
    Sends data to Kafka topic.
    """
    try:
        future = producer.send(KAFKA_TOPIC, value=data_dict)
        #result = future.get(timeout=10)  
        logging.info(f"Message sent to Kafka topic '{KAFKA_TOPIC}': {data_dict}")
    except KafkaError as e:
        logging.error(f"Failed to send message to Kafka: {e}")

def on_message(ws, message):
    """"
    Handles incoming WebSocket messages.
    """
    data = json.loads(message)
    if 'e' in data and data['e'] == 'kline':
        data_dict = {
            'ticker': data['s'],
            'price': data['k']['c'],
            'time': data['k']['T']  
        }
        logging.info(f"Processing data: {data_dict}")
        send_data_to_kafka(data_dict, ws.producer)

def on_open(ws):
    """" 
    Handles WebSocket connection opening and subscribes to the relevant streams. 
    """
    logging.info("WebSocket connection opened")
    subscribe_message = {
        "method": "SUBSCRIBE",
        "params": [f"{asset}@kline_1s" for asset in ASSET_LIST],
        "id": 1
    }
    ws.send(json.dumps(subscribe_message))
    logging.info(f"Subscribed to streams: {', '.join(ASSET_LIST)}")

def main():
    """
    Main entry point for the streaming application.
    """
    logging.info("Starting WebSocket publisher")

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda m: json.dumps(m).encode('ascii'),
        retries=5,
        request_timeout_ms=30000
    )
    ws = websocket.WebSocketApp(
        WEBSOCKET_URL,
        on_message=on_message,
        on_error=lambda ws, error: logging.error(f"WebSocket error: {error}"),
        on_close=lambda ws, code, msg: logging.info(f"WebSocket closed: {code} - {msg}"),
        on_open=on_open
    )
    ws.producer = producer
    try:
        ws.run_forever()
    finally:
        logging.info("Closing Kafka Producer...")
        producer.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    main()