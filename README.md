# Secure REST API Lab & Vulnerability Remediation (Work 1)

Student Name: LuoHaozhen
Student ID: 23320324

## Project Overview

This project contains a simple secure REST API developed with Python Flask.
The GitHub Actions CI pipeline automatically runs security scanning for source code.
We also reproduce, analyse and patch a Server-Side Template Injection (SSTI) vulnerability using Vulhub docker environment.

## 1. Secure REST API Implementation

This Flask API provides user login authentication with JWT session token. It implements basic security controls against common web attacks.

![CI Pipeline screenshot](https://raw.githubusercontent.com/USERNAME/REPO_NAME/main/screenshots/website_running.png)

### API Endpoints

1.POST `/auth/login`

- Purpose: User login, returns JWT access token
- Example curl command:
- curl -X POST [http://127.0.0.1:5000/auth/login](http://127.0.0.1:5000/auth/login) -H "Content-Type:application/json" -d "{"username":"admin","password":"TestPass123"}"

2.GET `/api/data`

- Purpose: Protected resource, requires valid JWT token in request header
- Example curl command with token:
- curl [http://127.0.0.1:5000/api/data](http://127.0.0.1:5000/api/data) -H "Authorization: Bearer REPLACE_WITH_YOUR_TOKEN"
- Without token: Server returns HTTP 401 Unauthorized.

3.GET `/api/userinfo/1`

- Purpose: Get user profile information, protected by token authentication
- curl [http://127.0.0.1:5000/api/userinfo/1](http://127.0.0.1:5000/api/userinfo/1) -H "Authorization: Bearer REPLACE_WITH_YOUR_TOKEN"

![CI Pipeline screenshot](https://raw.githubusercontent.com/USERNAME/REPO_NAME/main/screenshots/api_curl.png)

### Security Controls Implemented

1. Session authentication based on JWT token. Password is required to obtain token. Attackers cannot access protected resources without valid token.
2. Input validation to filter unexpected user input.
3. Protection against unauthorized access. Access to private API endpoints is blocked if no valid token exists.

### CI/CD Security Pipeline

GitHub Actions workflow automatically runs two security scans after each code push:

1. Bandit: Static Application Security Testing (SAST) for Python source code
2. Safety: Software Composition Analysis (SCA), scan vulnerable third-party packages.

![CI Pipeline screenshot](https://raw.githubusercontent.com/USERNAME/REPO_NAME/main/screenshots/actions_ci.png)

## 2. Vulnerability Analysis: CVE-2020-1938 Apache Tomcat Ghostcat (AJP File Inclusion)

### Vulnerability Description

CVE-2020-1938, also known as Ghostcat, is an arbitrary file inclusion vulnerability in Apache Tomcat.
Tomcat’s AJP protocol connector lacks sufficient parameter validation. Attackers can send malicious AJP packets to read arbitrary files on the server, including web source code and configuration files without authentication.

### Reproduction Steps

1. Navigate to vulhub tomcat CVE-2020-1938 folder: cd vulhub/tomcat/CVE-2020-1938

2. Start vulnerable docker environment: docker-compose up -d

3. Run exploit script to read `/WEB-INF/web.xml`: python ghostcat.py 127.0.0.1 8009 /WEB-INF/web.xml

The server returns full content of web.xml, which proves arbitrary file read vulnerability exists.

![CI Pipeline screenshot](https://raw.githubusercontent.com/USERNAME/REPO_NAME/main/screenshots/ghostcatbefore.png)

### Root Cause Analysis

Apache Tomcat enables AJP connector on port 8009 by default. The AJP protocol does not validate `req_attribute` parameters properly. Attackers can forge AJP requests to access any file under the web application directory. Sensitive source code and configuration can be leaked.

### Applied Fix

Remove the 8009 port forwarding rule in docker-compose.yml.
The modified docker-compose.yml:

```yaml
version: '2'
services:
  tomcat:
    image: vulhub/tomcat:9.0.30
    ports:
      - "8080:8080"
```

After removing port mapping, the AJP port 8009 cannot be accessed from the host machine.
Restart container:
docker-compose down
docker-compose up --build -d

### Fix Verification

Run the same exploit script again. The connection to port 8009 is refused.
No sensitive file content can be read. The vulnerability is patched, normal HTTP web service on port 8080 still works.

![CI Pipeline screenshot](https://raw.githubusercontent.com/USERNAME/REPO_NAME/main/screenshots/ghostcatafter.png)

![CI Pipeline screenshot](https://raw.githubusercontent.com/USERNAME/REPO_NAME/main/screenshots/website8080.png)
