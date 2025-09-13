# Ticket Booking System

A ticket booking system built with FastAPI, PostgreSQL, Redis, Kafka, Elasticsearch, and Prometheus.

## Features

- User authentication (JWT)
- Role-based access (admin, client)
- Show and ticket management
- Distributed booking with Redis locking
- Booking events via Kafka
- Search with Elasticsearch
- Monitoring with Prometheus & Grafana

## Prerequisites

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

## Setup Instructions

### 1. Clone the repository

```sh
git clone <your-repo-url>
cd ticket-booking
```

### 2. Configure Environment Variables

Copy the example environment file and edit as needed:

```sh
cp .env_example .env
```

Edit `.env` if you want to change any default settings (database, Redis, etc).

### 3. Build and Start Services

```sh
docker-compose up --build
```

This will start:
- FastAPI app (on [http://localhost:8000](http://localhost:8000))
- PostgreSQL (on port 5432)
- Redis (on port 6379)
- Elasticsearch (on port 9200)
- Kafka, Zookeeper, Debezium
- Prometheus (on port 9090)
- Grafana (on port 3000)
- Kafka UI (on port 8080)

### 4. API Documentation

Once running, access the API docs at:

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### 5. Useful Endpoints

- **Sign up:** `POST /sign-up`
- **Login:** `POST /login`
- **Get current user:** `GET /me` (requires Bearer token)
- **Assign admin role:** `POST /users/{user_id}/roles/{role_id}` (admin only)
- **Show management:** `/shows`
- **Ticket management:** `/tickets`
- **Booking:** `/bookings`

### 6. Assign Admin Role Example

1. Login as an admin and get your token.
2. Assign the admin role to a user (replace `<TOKEN>` and `<USER_ID>`):

```sh
curl -X POST "http://localhost:8000/users/<USER_ID>/roles/1" \
  -H "Authorization: Bearer <TOKEN>"
```

### 7. Monitoring

- Prometheus: [http://localhost:9090](http://localhost:9090)
- Grafana: [http://localhost:3000](http://localhost:3000)
- Kafka UI: [http://localhost:8080](http://localhost:8080)

### 8. Stopping the Project

```sh
docker-compose down
```

## Development

- Code is auto-reloaded in the container.
- To install new dependencies, add them to `requirements.txt` and rebuild the container.

## License

MIT