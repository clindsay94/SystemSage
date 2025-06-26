# System Sage

System Sage is a web application for system analysis, rewritten in Java 21 and Spring Boot 3.2 from the original Python application. It provides tools for managing BIOS profiles, scanning system inventory, and auditing developer environments.

## Technologies Used

*   **Backend:** Java 21, Spring Boot 3.2, Spring Data JPA
*   **Build:** Apache Maven
*   **Database:** H2 (in-memory)
*   **Frontend:** Thymeleaf, Bootstrap

## How to Run

1.  Make sure you have Java 21 and Maven installed.
2.  From the project root directory, run the following command:

    ```bash
    mvn spring-boot:run
    ```

3.  The application will be available at [http://localhost:8080](http://localhost:8080).

## Features

*   **Overclocker's Logbook:** A web interface to create, read, update, and delete BIOS profiles.
*   **System Inventory:** Scans and displays installed software on the host machine (Windows only).
*   **Developer Environment Audit:** (Placeholder) A feature to audit the developer environment for tools and configurations.

## REST API

The application also exposes a REST API for its services:

*   `GET /api/bios-profiles`: Get all BIOS profiles.
*   `GET /api/bios-profiles/{id}`: Get a specific BIOS profile.
*   `POST /api/bios-profiles`: Create a new BIOS profile.
*   `PUT /api/bios-profiles/{id}`: Update a BIOS profile.
*   `DELETE /api/bios-profiles/{id}`: Delete a BIOS profile.
*   `GET /api/system-inventory`: Get a list of installed software.
*   `GET /api/devenv-audit/components`: Get detected developer components.
*   `GET /api/devenv-audit/env-vars`: Get environment variables.
*   `GET /api/devenv-audit/issues`: Get identified issues.