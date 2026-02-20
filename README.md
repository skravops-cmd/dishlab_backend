# 🍽️ DishLab Backend API

DishLab is a RESTful backend API for managing cooking recipes with authentication, cuisine validation, and user-specific dashboards.

This project is built with **Flask**, **MongoDB**, and **JWT**, fully Dockerized, and designed with **environment-based configuration** (development vs staging).

---

## 🚀 Tech Stack

- Python 3.11
- Flask
- MongoDB (local) / Azure Cosmos DB (Mongo API)
- JWT Authentication
- Docker & Docker Compose
- Swagger (OpenAPI via Flasgger)

---

## ✨ Features

- User registration & login (JWT-based auth)
- Create, update, delete recipes
- Cuisine validation
- User dashboard (last 10 recipes)
- Read-only staging environment
- Swagger API documentation
- Smoke test script
- Dockerized for local & cloud use

---

## 🧱 Project Structure

```

dishlab_backend/
├── app/
│   ├── **init**.py        # App factory & config selection
│   ├── config.py          # Base / Dev / Stage configs
│   ├── extensions.py      # JWT, Bcrypt, Mongo
│   ├── routes/
│   │   ├── auth.py
│   │   └── receipts.py
├── docker-compose.dev.yml
├── docker-compose.stage.yml
├── Dockerfile
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── run.py
└── test_build.sh

````

---

## ⚙️ Configuration & Environments

The app uses **config subclasses** selected via `FLASK_ENV`.

| Environment | Config Class | Database | Writes |
|------------|--------------|----------|--------|
| Development | `DevConfig` | Local MongoDB | ✅ Enabled |
| Staging | `StageConfig` | Azure Cosmos DB | ❌ Read-only |

Config selection happens automatically:

```text
FLASK_ENV=development → DevConfig
FLASK_ENV=staging     → StageConfig
````

---

## 🛠️ Development Setup (Local)

### 1️⃣ Clone the repo

```bash
git clone https://github.com/skravops-cmd/dishlab-backend.git
cd dishlab_backend
```

---

### 2️⃣ Create env file

```bash
cp .env.example .env.dev
```

Edit `.env.dev` with your local secrets.

> ⚠️ `.env.dev` is ignored by git and must NOT be committed.

---

### 3️⃣ Run with Docker

```bash
docker compose -f docker-compose.dev.yml up --build
```

API will be available at:

```
http://localhost:8000
```

---

## ☁️ Staging Setup (Azure Cosmos DB)

Staging uses **Azure Cosmos DB (Mongo API)** in **read-only mode**.

```bash
docker compose -f docker-compose.stage.yml up --build
```

Requirements:

* Cosmos DB Mongo API endpoint
* Read-only database user
* TLS enabled

---

## 📚 API Documentation (Swagger)

Swagger UI is available at:

```
http://localhost:8000/docs
```

Authentication uses JWT Bearer tokens:

```
Authorization: Bearer <your_token>
```

---

## 🧪 Smoke Tests

The project includes a full API smoke test.

### Requirements

```bash
sudo apt install jq
```

### Run tests

```bash
./test_build.sh
```

This script validates:

* Auth flow
* JWT issuance
* Recipe creation
* Cuisine validation
* Dashboard limits
* Unauthorized access protection

---

## 🧑‍🍳 Supported Cuisines

* Italian
* Asian
* Mexican
* Indian
* American
* French
* Mediterranean

---

## 🔐 Security Notes

* Secrets are loaded **only from environment variables**
* No secrets are committed to Git
* Staging environment is enforced as **read-only**
* Mongo access is abstracted and centrally controlled

---

## 🗺️ TODOs  

### Core

* [ ] Add refresh tokens
* [ ] Pagination for dashboard
* [ ] Input validation with Marshmallow or Pydantic
* [ ] Centralized error handling

### Security

* [ ] Rate limiting (Flask-Limiter)
* [ ] Password strength enforcement
* [ ] JWT token revocation
* [ ] Audit logging

### Testing & Quality

* [ ] Pytest test suite
* [ ] Test database isolation
* [ ] GitHub Actions CI pipeline
* [ ] Code coverage reporting

### Cloud & Ops

* [ ] Azure App Service deployment
* [ ] Application Insights logging
* [ ] Metrics & monitoring

---

## 📄 License

MIT

```
