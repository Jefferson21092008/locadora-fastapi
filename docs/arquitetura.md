# Arquitetura da Locadora

Este documento apresenta a arquitetura atual da Locadora, mostrando como os principais componentes da aplicação se relacionam desde o frontend até o banco de dados e os serviços externos.

## Visão geral

A Locadora utiliza uma arquitetura em camadas para separar responsabilidades entre interface, API, regras de negócio e persistência de dados.

```mermaid
flowchart TD
    U[Usuário / Navegador]

    F[Frontend<br>HTML + CSS + JavaScript]

    API[FastAPI<br>Routers]

    DEP[Dependências<br>Autenticação e autorização]

    SCH[Pydantic Schemas<br>Validação]

    SER[Services<br>Regras de negócio]

    REP[Repositories<br>Acesso aos dados]

    ORM[SQLAlchemy]

    DB[(PostgreSQL<br>Neon)]

    JWT[JWT<br>Autenticação]

    EMAIL[Brevo API<br>E-mails]

    U --> F
    F --> API

    API --> DEP
    API --> SCH

    DEP --> JWT

    API --> SER
    SER --> REP
    REP --> ORM
    ORM --> DB

    SER --> EMAIL