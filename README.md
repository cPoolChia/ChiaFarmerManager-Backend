[![Build Status](https://ci.efullmakt.io/buildStatus/icon?job=efullmakt-backend%2Fmain&style=flat-square)](https://ci.efullmakt.io/job/efullmakt-backend/job/main/)

![Python](https://img.shields.io/badge/-Python-000000?style=for-the-badge&logo=Python)
![Docker](https://img.shields.io/badge/-Docker-000000?style=for-the-badge&logo=Docker)
![Jenkins](https://img.shields.io/badge/-Jenkins-000000?style=for-the-badge&logo=Jenkins)

# FastAPI Celery SQLAlchemy Boilerplate

A small boilerplate for backend projects on Python combining some usefull frameworks.

# How to run

## Docker

```
docker-compose up
```

## Tests

```
docker-compose -f docker-compose.test-cov.yml up -V --abort-on-container-exit --build
```

## Standalone

```
poetry run uvicorn app:app --reload
```
