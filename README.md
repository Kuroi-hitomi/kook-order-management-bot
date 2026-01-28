# Kook Order Management Bot

A Kook bot with a FastAPI backend designed to manage order workflows and order lifecycle for a Kook-based esports companion service.

This project was developed as part of operating an esports companion shop on the Kook platform. Although the club has temporarily paused operations for strategic adjustments, this system represents a complete, real-world backend and bot integration project, covering order submission, review, assignment, and completion.

---

## Features

- Order submission through Kook bot commands
- Order review and approval workflow
- Companion (player) assignment to orders
- Order status lifecycle management (created, reviewed, accepted, completed)
- RESTful backend API built with FastAPI
- Persistent storage using PostgreSQL and SQLAlchemy
- Database schema versioning with Alembic
- Containerized deployment with Docker Compose

---

## Tech Stack

- **Language:** Python
- **Bot Framework:** khl (Kook Python SDK)
- **Backend Framework:** FastAPI
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **HTTP Client:** httpx
- **Deployment:** Docker & Docker Compose

---

## Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI entry point
│   │   ├── models.py     # SQLAlchemy models
│   │   ├── schemas.py    # Pydantic schemas
│   │   └── db.py         # Database session setup
│   ├── alembic/          # Database migrations
│   └── alembic.ini
├── bot.py                # Kook bot entry
├── docker-compose.yml    # Service orchestration
├── .env.example          # Environment variable template
└── README.md

```
---

## Setup & Usage
1. **Clone the repository**
    ```
    git clone https://github.com/your-username/kook-order-management-bot.git
    cd kook-order-management-bot
    ```
---
2. **Configure environment variables**

    Create a .env file based on the provided example:
    ```
    cp .env.example .env
    ```

    Edit .env and fill in the required values:
    ```
    DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/dbname
    KOOK_TOKEN=your_kook_bot_token
    API_BASE_URL=http://localhost:8000
    ```
---
3. **Start services with Docker**
    ```
    docker-compose up --build
    ```
    This will start:
    - FastAPI backend service

    - PostgreSQL database

    - Kook bot service
---
4. **Interact with the bot**
    
    Once running, users can interact with the Kook bot to:

    - Create new orders

    - Review and approve pending orders

    - Accept orders as a companion

    - Mark orders as completed

    - Query order information

    (The specific bot commands are implemented in bot.py.)
---

## Notes 
- Sensitive configuration files such as .env are intentionally excluded from version control.
- This project focuses on backend logic and workflow design rather than frontend UI.
- The system is designed to reflect real operational requirements instead of a simple demo.

## License
This project is for educational and portfolio demonstration purposes.

---

---


# 中文说明（Chinese Description）

## 项目简介

本项目是一个 **基于 Kook 平台的陪玩订单管理系统**，由 **Kook 机器人 + FastAPI 后端服务** 组成，用于管理陪玩店的下单流程与订单生命周期。

该系统最初用于实际运营中的电竞陪玩店，覆盖了从下单、审核、接单到完成订单的完整业务流程。该项目完整体现了一个真实业务系统从需求设计到技术实现的全过程。

---

## 功能概览

- 通过 Kook 机器人进行订单创建
- 订单审核与状态流转
- 陪玩人员接单与绑定
- 订单完成与记录管理
- 基于 FastAPI 的 RESTful 后端接口
- 使用 PostgreSQL + SQLAlchemy 进行数据持久化
- Alembic 数据库迁移管理
- Docker Compose 一键部署

---

## 技术栈

- 编程语言：Python
- Kook 机器人框架：khl
- 后端框架：FastAPI
- 数据库：PostgreSQL
- ORM：SQLAlchemy
- 数据迁移：Alembic
- 容器化部署：Docker / Docker Compose

---

## 使用说明

1. 克隆仓库并配置 `.env` 文件  
2. 使用 Docker Compose 启动服务  
3. 通过 Kook 机器人指令进行订单操作  

该项目主要展示后端架构设计、业务建模能力以及机器人与服务端的协作流程。

---

## 说明

- 本项目不包含前端界面，重点在于业务流程与系统设计
- 所有敏感信息均通过环境变量配置，不会上传至仓库
- 项目代码结构与实现方式适合用于技术作品集展示

---