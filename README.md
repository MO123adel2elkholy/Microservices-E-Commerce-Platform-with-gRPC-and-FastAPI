# FastAPI Microservices with gRPC & Protocol Buffers

Three asynchronous FastAPI microservices communicating via **gRPC (Protocol Buffers)** for high-throughput inter-service communication and JWT authentication.

## Architecture

```
                         [ External Client / Frontend ]
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            │ HTTP (:8000)             │ HTTP (:8001)             │ HTTP (:8002)
            ▼                          ▼                          ▼
┌──────────────────────────┐ ┌──────────────────────────┐ ┌──────────────────────────┐
│  User Service            │ │  Product Service         │ │  Order Service           │
│  - FastAPI REST API      │ │  - FastAPI REST API      │ │  - FastAPI REST API      │
│  - JWT Auth (Login/Reg)  │ │  - Catalog Management    │ │  - Order Creation & List │
│  - Role Authorization    │ │  - In-Memory Data Store  │ │  - In-Memory Data Store  │
│  - gRPC Server (:50050)  │ │  - gRPC Server (:50051)  │ │  - Async gRPC Clients    │
└──────────────────────────┘ └──────────────────────────┘ └──────────────────────────┘
             ▲                                ▲                          │
             │                                └──── ValidateProduct ─────┤ (gRPC)
             └───────────────────────────────────── ValidateToken ───────┘ (gRPC)
```

## Port Map

| Service | HTTP Port | gRPC Port | Description |
| :--- | :---: | :---: | :--- |
| **User Service** | `8000` | `50050` | User registration, login, JWT issuance, token validation via gRPC |
| **Product Service** | `8001` | `50051` | Product catalog, pricing, inventory validation via gRPC |
| **Order Service** | `8002` | — | Order placement; calls User Service & Product Service via gRPC |

## Prerequisites

- Python 3.11+
- Virtual environment (`venv`) or Docker Desktop

## Quick Start

### Option A: Run with Docker Compose (Single Command)

```bash
docker compose up --build
```
This builds and launches all three microservices with automatic DNS networking and health checks.

---

### Option B: Run Locally with Python

#### 1. Activate Virtual Environment & Install Dependencies
```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Compile Protobuf Stubs
```powershell
python scripts/generate_proto.py
```

#### 3. Start User Service (Terminal 1)
```powershell
python -m user_service.main
```
*HTTP listening on `http://localhost:8000`, gRPC listening on `localhost:50050`.*

#### 4. Start Product Service (Terminal 2)
```powershell
python -m product_service.main
```
*HTTP listening on `http://localhost:8001`, gRPC listening on `localhost:50051`.*

#### 5. Start Order Service (Terminal 3)
```powershell
python -m order_service.main
```
*HTTP listening on `http://localhost:8002`, connects to User Service and Product Service over gRPC.*

---

## API Examples & End-to-End Workflow

### 1. Register a User (User Service)
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "password": "securepassword123",
    "full_name": "Jane Doe",
    "role": "customer"
  }'
```

### 2. Login to Get JWT Access Token
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "password": "securepassword123"
  }'
```
Response:
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user_id": "usr-xxxxxxxx",
  "email": "customer@example.com",
  "role": "customer",
  "full_name": "Jane Doe"
}
```

### 3. Browse Products (Product Service)
```bash
curl http://localhost:8001/products
curl http://localhost:8001/products/prod-001
```

### 4. Create an Order (Order Service)
*The Order Service calls User Service via gRPC to validate the Bearer token and Product Service via gRPC to validate inventory:*
```bash
curl -X POST http://localhost:8002/orders \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"product_id": "prod-001", "quantity": 2},
      {"product_id": "prod-002", "quantity": 1}
    ]
  }'
```

### 5. List Authenticated Orders
```bash
curl http://localhost:8002/orders \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

## Interactive API Documentation (Swagger)

- **User Service Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Product Service Docs**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **Order Service Docs**: [http://localhost:8002/docs](http://localhost:8002/docs)

---

## Running the Automated Test Suite

```powershell
# Run all tests
.\venv\Scripts\pytest.exe -v

# Run specific service test suites
.\venv\Scripts\pytest.exe tests/test_user_service.py -v
.\venv\Scripts\pytest.exe tests/test_product_service.py -v
.\venv\Scripts\pytest.exe tests/test_order_service.py -v
```

---

## Project Structure

```
├── proto/                         # Shared Protobuf schemas
│   ├── product.proto              # Product catalog & stock validation RPCs
│   └── user.proto                 # User token validation & profile RPCs
├── user_service/                  # User & Auth Microservice (:8000 HTTP / :50050 gRPC)
│   ├── generated/                 # Compiled Protobuf stubs
│   ├── main.py                    # FastAPI app + gRPC server lifespan
│   ├── grpc_server.py             # UserServicer (ValidateToken, GetUser)
│   ├── security.py                # Bcrypt password hashing & PyJWT tokens
│   ├── models.py                  # Pydantic schemas (Login, Register, Token)
│   ├── store.py                   # In-memory user repository
│   ├── config.py                  # Environment configurations
│   └── Dockerfile
├── product_service/               # Product Microservice (:8001 HTTP / :50051 gRPC)
│   ├── generated/                 # Compiled Protobuf stubs
│   ├── main.py                    # FastAPI app + gRPC server lifespan
│   ├── grpc_server.py             # ProductServicer (GetProduct, ValidateProduct)
│   ├── models.py                  # Pydantic product schemas
│   ├── store.py                   # In-memory product catalog
│   ├── config.py                  # Environment configurations
│   └── Dockerfile
├── order_service/                 # Order Microservice (:8002 HTTP)
│   ├── main.py                    # FastAPI app with gRPC auth & stock validation
│   ├── grpc_client.py             # Async gRPC client for Product Service
│   ├── grpc_auth_client.py        # Async gRPC client for User Service
│   ├── models.py                  # Pydantic order schemas
│   ├── store.py                   # In-memory order storage
│   ├── config.py                  # Environment configurations
│   └── Dockerfile
├── tests/                         # Automated tests
│   ├── test_user_service.py       # User auth & token validation tests
│   ├── test_product_service.py    # Product catalog unit tests
│   └── test_order_service.py      # Order auth enforcement tests
├── scripts/
│   └── generate_proto.py          # Cross-platform Protobuf compiler
├── docker-compose.yml             # Multi-service container orchestration
├── requirements.txt               # Categorized project dependencies
└── plan.md                        # Master implementation plan & task matrix
```
