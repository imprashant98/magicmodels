<div align="center">
  <h1>✨ python-magicmodels ✨</h1>
  <p><strong>A blazingly fast CLI tool to instantly generate production-ready Django and FastAPI APIs from a simple schema.</strong></p>

  [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
  [![Python Versions](https://img.shields.io/pypi/pyversions/python-magicmodels.svg)](https://pypi.org/project/python-magicmodels/)
  [![Frameworks](https://img.shields.io/badge/Frameworks-Django%20%7C%20FastAPI-success.svg)](#)
</div>

---

## 🚀 What is python-magicmodels?

`python-magicmodels` translates a single, human-readable `.txt` file into a full, scalable, **Domain-Driven** backend architecture. 

It completely removes the boilerplate of setting up APIs by automatically generating:
- **Models, Serializers/Schemas, & Routers** isolated per domain.
- **Pagination, Searching, & Sorting** out-of-the-box.
- **Security & Permissions** templates built-in.
- **Dockerization** (`Dockerfile` & `docker-compose.yml`) ready for deployment.

Whether you're spinning up an MVP or setting up microservices, `python-magicmodels` gives you a 100% working backend in seconds.

## 📦 Installation

Install globally via `pip`:

```bash
pip install python-magicmodels
```

## ⚡ How to Use

### 1. Define your Database Schema
Create a file named `schema.txt`. Use our intuitive schema syntax to define your data models and relationships.

```text
Model: Author
- name (String)
- email (String) [indexed]
- bio (Text)

Model: Book
- title (String)
- published_date (DateTime)
- author (Author)
```

### 2. Generate the Magic!
Run the `magicmodels` command on your terminal. You can choose either `--framework django` or `--framework fastapi`.

**Generate a Django REST Framework API:**
```bash
magicmodels schema.txt --framework django --output ./my_django_api
```

**Generate a FastAPI Project:**
```bash
magicmodels schema.txt --framework fastapi --output ./my_fastapi_api
```

### 3. Spin it up!
The generated project is fully Dockerized. Navigate to your output directory and run Docker Compose:
```bash
cd my_django_api
docker-compose up --build
```
Your production-ready API is now live! 

*(For FastAPI, visit `http://localhost:8000/docs` to see your auto-generated Swagger UI!)*

---

## 📖 Schema Syntax Guide

The parser is strict but extremely simple. 

- **Models**: Declare a model with `Model: YourModelName`.
- **Fields**: Declare a field with `- field_name (Type) [Modifiers]`.

### Supported Data Types
* `String` (255 max length)
* `Text` (Unlimited length)
* `Int`
* `Boolean`
* `DateTime`

### Supported Modifiers
Modifiers are optional tags you can add to the end of a field definition:
* `[pk]`: Marks the field as a Custom Primary Key.
* `[indexed]`: Adds a database index for faster lookups.

### Relationships
Relationships are detected automatically based on the type you provide!
* **One-to-Many (ForeignKey)**: Simply put the target Model name in parentheses. E.g., `- author (Author)`
* **Many-to-Many**: Wrap the target Model name in `list[]`. E.g., `- tags (list[Tag])`

### Full Schema Example
```text
Model: User
- id (Int) [pk]
- username (String) [indexed]
- is_active (Boolean)

Model: Post
- title (String)
- content (Text)
- author (User)

Model: Tag
- name (String) [indexed]
- posts (list[Post])
```

## 🛠️ Advanced Features Automatically Included

Regardless of which framework you choose, `python-magicmodels` embeds advanced API functionality:
1. **Pagination**: Endpoints are natively paginated.
2. **Dynamic Searching**: Any field marked as a `String` or `Text` is automatically searchable via `?search=keyword`.
3. **Sorting**: All models support ascending/descending sorts out of the box via `?sort_by=field&order=desc`.
4. **Permissions**: Mutation endpoints (`POST`, `PATCH`, `DELETE`) are scaffolded with authentication dependencies/permissions ready to be customized for your exact business logic.

## 🤝 Contributing
Contributions are always welcome! Feel free to open an issue or submit a Pull Request if you want to add support for a new framework or feature.