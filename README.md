# Streaming Project

A real-time cryptocurrency price streaming application using Python, Redpanda (a Kafka-compatible streaming platform), and PostgreSQL. All services are containerized and managed with Docker Compose.

## Table of Contents

- [Description](#description)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Dependencies](#dependencies)
- [Contributing](#contributing)
- [License](#license)

## Description

This project demonstrates a complete, real-time data streaming pipeline. A `publisher` service connects to the Binance WebSocket API to stream 1-second cryptocurrency candlestick data, which it then publishes to a Redpanda topic. A `consumer` service subscribes to this topic, processes the incoming data using the `quixstreams` library, and persists the aggregated data into a PostgreSQL database.

The entire stack is designed to run within Docker containers, making it easy to set up, run, and scale.

## Architecture

The data flows through the system as follows:

`Binance WebSocket API` -> `Python Publisher (publisher.py)` -> `Redpanda (Kafka Topic)` -> `Python Consumer (consumer.py)` -> `PostgreSQL Database`

All services (`publisher`, `consumer`, `redpanda`, `db`, `console`, `pgadmin`) are defined in the `docker-compose.yml` file. The stack also includes two web-based UIs for easy management and monitoring:
- **Redpanda Console**: For viewing Kafka topics, messages, and broker status.
- **pgAdmin**: For managing and querying the PostgreSQL database.

## Features

- **Real-time Data Ingestion**: Streams 1-second candlestick data from the Binance API.
- **Data Publishing**: A Python producer (`publisher.py`) sends the collected data to a Redpanda topic using `kafka-python-ng` library.
- **Stream Processing**: A Python consumer (`consumer.py`) uses the `quixstreams` library to process the data stream.
- **Data Persistence**: Processed data is stored in a PostgreSQL database for further analysis.
- **Containerized**: Fully containerized with Docker and Docker Compose for easy deployment and scalability.
- **Scalable Kafka-alternative**: Uses Redpanda, a modern, high-performance, Kafka-compatible streaming platform.
- **Management UIs**: Includes Redpanda Console and pgAdmin for easy monitoring and administration.

## Prerequisites

Before you begin, ensure you have the following installed on your system:
- Docker
- Docker Compose (usually included with Docker Desktop)

## Getting Started

1.  **Clone the repository:**
    ```bash
    git clone DchemistRae/streaming_pipeline.git
    cd streaming_pipeline
    ```

2.  **OPTIONAL: Configure the environment: (only do these if you require a different set of cryptocurrenciy prices or different configuration)**
    Create a `.env` file in the project root. This file is optional; if it's not present, the application will use the default values from the `docker-compose.yml` file. You can copy and paste the following as a starting point:
    ```bash
    
    # Redpanda/Kafka Configuration
    KAFKA_BROKER=redpanda-0:9092 # Use 'localhost:19092' to connect from your host machine
    KAFKA_TOPIC=crypto_prices

    # Binance WebSocket Configuration
    ASSET_LIST=btcusdt,ethusdt,solusdt,xrpusdt

    # PostgreSQL Configuration
    POSTGRES_USER=postgres
    POSTGRES_PASSWORD=postgres
    POSTGRES_DB=crypto_db
    POSTGRES_HOST=db 
    POSTGRES_PORT=5432
    ```
    > **Note**: Configuring the environment is optional, you do not need to provide any configuration and the app will run with default values.

## Configuration

The application is configured using environment variables, which can be placed in a `.env` file in the project root, an example .env file is provided.


| Variable            | Description                                                              | Default Value |
|---------------------|--------------------------------------------------------------------------|----------------------------|
| `KAFKA_BROKER`      | The address of the Redpanda/Kafka broker.                                | `redpanda-0:9092`          |
| `KAFKA_TOPIC`       | The topic to publish and consume messages from.                          | `crypto_prices`            |
| `ASSET_LIST`        | Comma-separated list of crypto assets to track (e.g., `btcusdt,ethusdt`).| `btcusdt,ethusdt,solusdt`  |
| `WEBSOCKET_URL`     | The Binance WebSocket URL for data streaming.                            | `wss://stream.binance.com:9443/ws` |
| `POSTGRES_USER`     | PostgreSQL username.                                                     | `postgres`                 |
| `POSTGRES_PASSWORD` | PostgreSQL password.                                                     | `postgres`                 |
| `POSTGRES_DB`       | The name of the PostgreSQL database.                                     | `crypto_db`                |
| `POSTGRES_HOST`     | The hostname of the PostgreSQL server (for container-to-container comms).| `db`                       |
| `POSTGRES_PORT`     | The port for the PostgreSQL server.                                      | `5432`                     |

## Usage

1.  **Start the services:**
    Run the following command from the project root to build and start all services in detached mode.
    ```bash
    docker compose up --build -d
    ```
    This will start the `publisher`, `consumer`, `redpanda` cluster, `postgres` database, and the web UIs.

2.  **Verify Data in Redpanda Console**
    Open your browser and navigate to `http://localhost:8080`.
    From the left-hand menu, go to the **Topics** page. You should see the `crypto_prices` topic. Click on it to view the live stream of messages being published.

    ![Screenshot](/screenshots/redpanda.png "Redpanda UI")

3.  **Verify Data in PostgreSQL with pgAdmin**

    You can connect to the PostgreSQL database using the pgAdmin web client.

    1.  **Open pgAdmin**: Navigate to `http://localhost:5050` in your browser.
    2.  **Login**: Use the default credentials to log in:
        -   **Email**: `admin@example.com`
        -   **Password**: `admin`
    3.  **Add a New Server**:
        -   Right-click on "Servers" in the left-hand browser tree and select `Register -> Server...`.
        -   In the **General** tab, give your server a name (e.g., "Crypto-DB").
        -   Switch to the **Connection** tab and fill in the details. Use the default values from the `Configuration` section unless you have customized them in your `.env` file.

        | Setting              | Value                               |
        |----------------------|-------------------------------------|
        | Host name/address    | `db`                                |
        | Port                 | `5432`                              |
        | Maintenance database | `postgres`                          |
        | Username             | `postgres` (or your `POSTGRES_USER`)  |
        | Password             | `postgres` (or your `POSTGRES_PASSWORD`)|

        -   Click **Save**.
    4.  **Query Data**: You can now expand the server, navigate to `Databases -> crypto_db -> Schemas -> public -> Tables`, right-click on the `crypto_prices` table, and select `View/Edit Data -> All Rows` to see the data being inserted by the consumer.

    ![Screenshot](/screenshots/pgadmin.png "pgadmin UI")

4.  **Verify Data via CLI (Optional)**

    Alternatively, you can connect directly to the PostgreSQL container to verify that data is being saved.
    ```bash
    # Connect to psql inside the container
    docker compose exec -it db psql -U postgres -d crypto_db

    # Inside psql, check the table
    \dt
    SELECT * FROM crypto_prices LIMIT 10;
    ```

5.  **Check Logs**
    To monitor the real-time logs from the publisher or consumer services:
    ```bash
    # View publisher logs
    docker compose logs -f publisher

    # View consumer logs
    docker compose logs -f consumer
    ```

6.  **Stop the Services**
    To stop and remove the containers, run:
    ```bash
    docker compose down
    ```

## Project Structure
```
.
├── consumer.py         # Consumes data from Kafka, processes, and saves to DB
├── docker-compose.yml  # Defines and configures all services
├── Dockerfile          # Builds the Python application container
├── publisher.py        # Fetches data from Binance and publishes to Kafka
├── README.md           
├── requirements.txt    # Python dependencies
└── screenshots/        # Contains UI screenshots
```

## Dependencies

The main dependency for this project is:
- **Quixstreams**: A Python library for stream processing, built on the logic of pandas, but for streaming data.
- **kafka-python-ng**: A Python native library for the Apache Kafka used to publish data to Kafka topic.
- **psycopg2-binary**: PostgreSQL adapter for Python.
- **websocket-client**: A WebSocket client for Python to connect to the Binance API.

A full list of dependencies is available in the `requirements.txt` file.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any changes.

