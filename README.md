# 🛒 E-Commerce API

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)(https://www.python.org/)
![Django](https://img.shields.io/badge/Django-4.x-green.svg)(https://www.djangoproject.com/)
![DRF](https://img.shields.io/badge/Django_REST_Framework-3.x-red.svg)(https://www.django-rest-framework.org/)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg)(https://www.docker.com/)

A robust, scalable, and fully containerized RESTful API designed to power modern e-commerce platforms. Built with **Django** and **Django REST Framework (DRF)**, this backend handles everything from user authentication and product catalog management to shopping cart operations.

The project is fully containerized with **Docker** for seamless deployment and features comprehensive unit testing using Django's native `TestCase` and `SimpleTestCase` to ensure high code reliability.

---

## ✨ Key Features

- 🔐 **Secure Authentication**: JWT-based authentication with role-based access control (Admin, Customer).
- 📦 **Product Catalog**: Full CRUD operations for products and categories, including filtering, searching.
- 🛒 **Shopping Cart & Orders**: Dynamic cart management and order history with status tracking.
- 🐳 **Dockerized Environment**: Fully containerized with Docker and Docker Compose for consistent development and production environments.
- 🧪 **Comprehensive Testing**: Unit test coverage using Django's `SimpleTestCase` and `TestCase`
- 📝 **Auto-Generated Docs**: Interactive API documentation powered by **drf-spectacular** and **Swagger**.

---

## 🛠️ Tech Stack

| Category      | Technologies                        |
| ------------- | ----------------------------------- |
| **Language**  | Python 3.12                         |
| **Framework** | Django, Django REST Framework       |
| **Database**  | PostgreSQL                          |
| **Container** | Docker, Docker Compose              |
| **Testing**   | Django `TestCase`, `SimpleTestCase` |
| **Auth**      | Django Simple JWT                   |
| **Docs**      | Swagger                             |

---

## 🚀 Getting Started

The easiest way to run this project is using Docker.

### Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/)

### 🐳 Docker Setup (Recommended)

1. **Clone the repository:**

   ```bash
   git clone https://github.com/PouyaKhDev/E-commerce-API.git
   ```

2. **Set up docker environment variables**
   Create a .env file in the root directory and set:

   ```env
   DEV=[true/false]
   API_PORT=[port, eg: 8000]
   TAG_DB=18-alpine
   POSTGRES_DB=[postgres db name, eg: devdb]
   POSTGRES_USER=[postgres user's username, eg: devuser]
   POSTGRES_PASSWORD=[postgres user's password, eg: devpass]
   ```

3. **Set up project environment variables**
   Create an env directory and an api.env file inside of it and set:

   ```env
   DEBUG=[True/False]
   SECRET_KEY=[a random secure secret key]
   ALLOWED_HOSTS=[allowed hosts eg: localhost,127.0.0.1]
   SITE_ID=[eg: 1]

   DB_HOST=db
   DB_NAME=[same as POSTGRES_DB in previous env file]
   DB_USER=[same as POSTGRES_USER in previous env file]
   DB_PASS=[same as POSTGRES_PASSWORD in previous env file]
   ```

4. **Build and run the containers**

   ```bash
   docker compose up --build
   ```

5. **Create a superuser (optional)**

   ```bash
   docker compose run --rm app sh -c "python manage.py createsuperuser"
   ```

6. **Open the server**
   open "http://127.0.0.1:8000/api/docs/" in a web browser.

   Note: the url is based on environment variables ALLOWED_HOSTS in env/api.env file and API_PORT in .env file.
