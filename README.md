# USEA Homework 2 - CI/CD Pipeline with Jenkins, GitHub, Docker & Docker Swarm on AWS

**Course:** Advanced Cloud Technology  
**Lecturer:** Mr. Krol Noeurn  
**Student:** TONN Sievphor  
**GitHub Repository:** [https://github.com/Sievphor/cloud_home_work_2.git](https://github.com/Sievphor/cloud_home_work_2.git)  
**Academic Year:** 2026 - 2027  

---

## 1. Project Overview
This project implements a fully automated Continuous Integration and Continuous Deployment (CI/CD) pipeline on AWS. Every change pushed to GitHub automatically triggers Jenkins to build a container image, push it to a private Amazon ECR repository with a traceable tag, and deploy it across a Docker Swarm cluster running on Amazon EC2 with zero downtime.

---

## 2. System Architecture

```text
Developer (git push)
       │
       ▼
GitHub Repository (https://github.com/Sievphor/cloud_home_work_2.git)
       │ (Webhook trigger)
       ▼
Jenkins Pipeline Server
       │
       ├─► 1. Checkout source code
       ├─► 2. Authenticate with AWS ECR (`aws ecr get-login-password`)
       ├─► 3. Build & tag Docker image (`${BUILD_NUMBER}-${GIT_COMMIT}`)
       ├─► 4. Push immutable image to Amazon ECR
       └─► 5. SSH to Swarm Manager & execute `docker stack deploy`
                               │
                               ▼
               Docker Swarm Cluster (Amazon EC2)
               ┌──────────────────────────────────────────────┐
               │  Swarm Manager:  http://13.220.98.249:8898   │
               │  Swarm Worker 1: http://34.229.219.41:8898   │
               │  Swarm Worker 2: http://54.90.208.206:8898   │
               │  Rolling Update (Replicas: 3)                │
               └──────────────────────────────────────────────┘
```

---

## 3. Technologies Used
- **Version Control:** GitHub (Git)
- **CI/CD Automation:** Jenkins Pipeline (Pipeline as Code)
- **Container Engine:** Docker & Docker Buildx
- **Container Registry:** Amazon Elastic Container Registry (ECR)
- **Container Orchestration:** Docker Swarm on AWS EC2 (1 Manager + 2 Workers)
- **Base Infrastructure:** Amazon Web Services (AWS EC2, VPC, IAM, Security Groups)

---

## 4. Local Testing Before Cloud Deployment

Before pushing to AWS, verify the Docker image locally:

```bash
# Build the Docker image locally
docker build -t sievphor-homework2:local .

# Run the container locally
docker run -d --name local-test -p 8898:80 sievphor-homework2:local

# Verify the container is running and serving traffic
curl http://localhost:8898
# or open in browser: http://localhost:8898

# Clean up
docker stop local-test && docker rm local-test
```

---

## 5. Amazon ECR & AWS Configuration
- **AWS Region:** `us-east-1`
- **AWS Account ID:** `908157891706`
- **ECR Repository:** `sievphor-homework2`
- **ECR Registry URI:** `908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework2`
- **Tagging Strategy:** `${BUILD_NUMBER}-${GIT_COMMIT:0:7}` and `latest`

---

## 6. Docker Swarm Cluster Setup on EC2

### Manager Node Setup (`13.220.98.249`)
```bash
# Initialize Swarm on Manager EC2
docker swarm init --advertise-addr 172.31.29.236

# Obtain worker join token
docker swarm join-token worker
```

### Worker 1 (`34.229.219.41`) & Worker 2 (`54.90.208.206`) Setup
```bash
# Run on each Worker EC2
docker swarm join --token <SWARM_WORKER_TOKEN> 172.31.29.236:2377
```

### Security Group Ingress Rules
- **Port 22 (SSH):** Jenkins server IP / Admin IP
- **Port 8898 (HTTP):** Anywhere (`0.0.0.0/0`) for application access
- **Port 2377/tcp:** Cluster management communication
- **Port 7946/tcp & udp:** Node-to-node communication
- **Port 4789/udp:** Overlay network traffic

---

## 7. Swarm Stack Deployment & Verification

Deploying the stack:
```bash
docker stack deploy --with-registry-auth -c docker-stack-deploy.yml homework2
```

Verification commands:
```bash
# List nodes in the cluster
docker node ls

# List active stacks
docker stack ls

# Check service status and replicas (3/3)
docker stack services homework2

# Check task placement and rolling update history
docker service ps homework2_web
```

---

## 8. Live Application Endpoints
- **Manager:** `http://13.220.98.249:8898`
- **Worker 1:** `http://34.229.219.41:8898`
- **Worker 2:** `http://54.90.208.206:8898`

All nodes respond through Swarm's ingress routing mesh.
