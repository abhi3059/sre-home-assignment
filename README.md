# Rick and Morty SRE Application

A highly available, scalable, and production-grade RESTful application that integrates with the [Rick and Morty API](https://rickandmortyapi.com/). Built with SRE and DevOps best practices in mind, and deployed on Kubernetes using Helm and GitHub Actions.

---

## 📌 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Setup & Deployment](#setup--deployment)
  - [Local Development](#local-development)
  - [Kubernetes Deployment](#kubernetes-deployment)
- [API Documentation](#api-documentation)
- [Health Check](#health-check)
- [Monitoring & Observability](#monitoring--observability)
- [CI/CD Pipeline](#cicd-pipeline)
- [Helm Chart Configuration](#helm-chart-configuration)
- [Testing](#testing)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

---

## ✅ Overview

This application queries the Rick and Morty API to fetch alive human characters originating from Earth (any variant), caches the result in Redis with TTL, persists the data into PostgreSQL, and exposes RESTful APIs with pagination, sorting, and health endpoints.

---

## 📐 Architecture

```mermaid
graph TD
    Dev[Developer] -->|Push| GitHub
    GitHub -->|CI/CD| GitHubActions
    GitHubActions -->|Docker Build & Push| DockerHub
    GitHubActions -->|Deploy via Helm| KindCluster[(Kubernetes Cluster)]
    KindCluster -->|Run| AppPod(FastAPI App)
    AppPod --> Redis
    AppPod --> Postgres
    AppPod --> Jaeger
    AppPod --> Metrics[Prometheus Exporter]

