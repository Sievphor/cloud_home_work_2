# សាកលវិទ្យាល័យ សៅស៍អុីសថ៍អេយេសៀ (UNIVERSITY OF SOUTH-EAST ASIA)
## មហាវិទ្យាល័យវិទ្យាសាស្ត្រ និងបច្ចេកវិទ្យា (Faculty of Science and Technology)

---

# Homework 2: CI/CD with Jenkins, GitHub, Docker & Docker Swarm on AWS EC2
### របាយការណ៍ស្វ័យប្រវត្តិកម្ម CI/CD Pipeline លើ Amazon Web Services

- **Course:** Advanced Cloud Technology
- **Lecturer:** Mr. Krol Noeurn
- **Student Name:** TONN Sievphor
- **GitHub Repository:** https://github.com/Sievphor/cloud_home_work_2.git
- **Academic Year:** 2026 - 2027

---

## ១. សេចក្តីផ្តើម (Introduction)
គម្រោងនេះមានគោលបំណងបង្កើតប្រព័ន្ធស្វ័យប្រវត្តិកម្ម Continuous Integration និង Continuous Deployment (CI/CD) ពេញលេញមួយនៅលើបរិស្ថាន Cloud (AWS) ដោយប្រើប្រាស់បច្ចេកវិទ្យា GitHub, Jenkins, Docker, Amazon ECR និង Docker Swarm នៅលើ Amazon EC2។

នៅក្នុងប្រព័ន្ធនេះ នៅពេលណាដែល Developer ធ្វើការ Push Code ថ្មីទៅកាន់ GitHub Repository (`cloud_home_work_2`) នោះ GitHub Webhook នឹងផ្ញើសញ្ញា (Trigger) ទៅកាន់ Jenkins Server ដោយស្វ័យប្រវត្តិ។ Jenkins នឹងធ្វើការទាញយកកូដ (Checkout), ផ្ទៀងផ្ទាត់សិទ្ធិជាមួយ Amazon ECR, កសាង (Build) Docker Image និងបំពាក់ស្លាកសម្គាល់ (Tag) ជាមួយ Build Number និង Commit Hash រួចបញ្ជូន (Push) ទៅកាន់ Amazon ECR។ បន្ទាប់មក Jenkins នឹងភ្ជាប់ទៅកាន់ Swarm Manager តាមរយៈ SSH ដើម្បីធ្វើការ Deploy ឬ Update សេវាកម្មនៅលើ Docker Swarm Cluster (១ Manager + ២ Workers) ដោយប្រើបច្ចេកទេស Rolling Update ដោយមិនមានការរអាក់រអួលដល់អ្នកប្រើប្រាស់ឡើយ (Zero-downtime deployment)។

---

## ២. ស្ថាបត្យកម្មប្រព័ន្ធ (System Architecture)

```
[Developer] 
    │ git push
    ▼
[GitHub Repository] ────────(Webhook Notification)────────► [Jenkins CI/CD Server]
https://github.com/Sievphor/cloud_home_work_2.git                   │
                                                                    │
    ┌───────────────────────────────────────────────────────────────┘
    │ 1. Checkout Code
    │ 2. ECR Authentication (aws ecr get-login-password)
    │ 3. Docker Buildx (linux/amd64)
    │ 4. Docker Push with Build Tag & Commit SHA
    ▼
[Amazon ECR Repository (Private)]
URI: 908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework2
    │
    │ 5. SSH Remote Execution: docker stack deploy --with-registry-auth
    ▼
[Docker Swarm Cluster on AWS EC2]
    ├── Swarm Manager (13.220.98.249:8898)  ◄── Pulls latest image from ECR
    ├── Swarm Worker 1 (34.229.219.41:8898) ◄── Ingress Routing Mesh & Shared Load
    └── Swarm Worker 2 (54.90.208.206:8898) ◄── Ingress Routing Mesh & Shared Load
```

---

## ៣. ការអនុវត្តការងារតាមជំហាន (Step-by-Step Implementation)

### ជំហានទី ១៖ បង្កើត GitHub Repository
- បង្កើត GitHub Repository ឈ្មោះ `cloud_home_work_2` (Link: https://github.com/Sievphor/cloud_home_work_2.git)។
- រៀបចំរចនាសម្ព័ន្ធឯកសារ៖
  - `index.html`: កូដកម្មវិធី Frontend បង្ហាញព័ត៌មាននិស្សិត TONN Sievphor និងស្ថានភាព Deployment លើ Port 8898
  - `Dockerfile`: កំណត់ Base Image និងបរិស្ថានរបស់ Container
  - `Jenkinsfile`: កូដកំណត់ដំណាក់កាល Pipeline (Pipeline as Code)
  - `docker-stack.yml`: កំណត់ Services, Replicas ចំនួន 3, Placement និង Rolling Update
  - `.gitignore`: មិនបញ្ចូល Secrets, `.pem`, `.token` ទៅកាន់ Git
  - `README.md`: សៀវភៅណែនាំគម្រោង

### ជំហានទី ២៖ សរសេរ Dockerfile និងតេស្តលើ Local Machine
- ប្រើប្រាស់ Base Image `nginx:alpine` ដែលមានទំហំតូច សុវត្ថិភាព និងល្បឿនលឿន។
- ពាក្យបញ្ជាតេស្តលើ Local Machine៖
  ```bash
  docker build -t sievphor-homework2:local .
  docker run -d -p 8898:80 --name test-app sievphor-homework2:local
  curl http://localhost:8898
  ```
- កម្មវិធីដំណើរការបានត្រឹមត្រូវ និងឆ្លើយតបលើ Port 8898 មុនពេលរុញទៅ AWS។

### ជំហានទី ៣៖ បង្កើត Amazon ECR Private Repository
- បង្កើត Private Repository នៅលើ Amazon ECR ក្នុងតំបន់ (Region) `us-east-1`៖
  - **Account ID:** `908157891706`
  - **Repository Name:** `sievphor-homework2`
  - **URI:** `908157891706.dkr.ecr.us-east-1.amazonaws.com/sievphor-homework2`
- កំណត់ Tag Immutability ដើម្បីធានាសុវត្ថិភាពមិនឱ្យមានការសរសេរជាន់លើរូបភាពចាស់។

### ជំហានទី ៤៖ កំណត់រចនាសម្ព័ន្ធ Jenkins Pipeline & Webhook
- បង្កើត Jenkins Pipeline Job ដោយជ្រើសរើស **Pipeline script from SCM** (Git: `https://github.com/Sievphor/cloud_home_work_2.git`)។
- បន្ថែម Credentials ក្នុង Jenkins:
  - `aws-credentials`: AWS Access Key ID និង Secret Access Key សម្រាប់ Push/Pull ECR
  - `swarm-ssh-key`: SSH Private Key សម្រាប់ Login ទៅកាន់ Swarm Manager EC2 (`13.220.98.249`)
- កំណត់ GitHub Webhook:
  - Payload URL: `http://<JENKINS_PUBLIC_IP>:8080/github-webhook/`
  - Content type: `application/json`
  - Events: `Just the push event`

### ជំហានទី ៥៖ បង្កើត Docker Swarm Cluster លើ AWS EC2
- បង្កើត EC2 Instances ចំនួន ៣ (Ubuntu 22.04 LTS):
  1. `Swarm-Manager`: `13.220.98.249`
  2. `Swarm-Worker1`: `34.229.219.41`
  3. `Swarm-Worker2`: `54.90.208.206`
- នៅលើ Manager Node:
  ```bash
  sudo docker swarm init --advertise-addr 13.220.98.249
  ```
- នៅលើ Worker Nodes:
  ```bash
  sudo docker swarm join --token <WORKER_JOIN_TOKEN> 13.220.98.249:2377
  ```
- ផ្ទៀងផ្ទាត់ Cluster តាមរយៈ `docker node ls`៖ បង្ហាញ Manager (Leader) និង Workers ទាំងពីរក្នុងស្ថានភាព `Ready` / `Active`។

### ជំហានទី ៦៖ កំណត់ Security Group លើ AWS EC2
- **Port 22 (SSH):** អនុញ្ញាតសម្រាប់ Jenkins IP / Admin IP
- **Port 8898 (HTTP):** អនុញ្ញាត `0.0.0.0/0` ដើម្បីឱ្យសាធារណជនចូលមើល Web App បាន
- **Port 2377 (TCP):** Cluster Management Communication
- **Port 7946 (TCP/UDP):** Node-to-node communication
- **Port 4789 (UDP):** Overlay network traffic

### ជំហានទី ៧៖ Deploy Stack និងផ្ទៀងផ្ទាត់ Rolling Update
- នៅពេល Jenkins Deploy តាមរយៈ `docker stack deploy --with-registry-auth -c /tmp/docker-stack-deploy.yml homework2`៖
  - Service ដំណើរការជាមួយ `replicas: 3` (រត់ចែកគ្នានៅលើ Manager, Worker 1 និង Worker 2)
  - ការ Update ធ្វើឡើងតាម `update_config`:
    - `parallelism: 1`: Update ម្តងមួយ container
    - `delay: 10s`: រង់ចាំ ១០ វិនាទីមុននឹងបន្ត container បន្ទាប់
    - `order: start-first`: បង្កើត container ថ្មីឱ្យដំណើរការជាមុន ទើបបិទ container ចាស់
- ផ្ទៀងផ្ទាត់តាមរយៈពាក្យបញ្ជា៖
  ```bash
  docker stack ls
  docker stack services homework2
  docker service ps homework2_web
  ```

### ជំហានទី ៨៖ ផ្ទៀងផ្ទាត់ការចូលប្រើប្រាស់ផ្ទាល់ (Live Reachability)
- ចូលមើលតាម Web Browser៖
  - Swarm Manager: `http://13.220.98.249:8898`
  - Swarm Worker 1: `http://34.229.219.41:8898`
  - Swarm Worker 2: `http://54.90.208.206:8898`
- អរគុណដល់ Docker Swarm Ingress Routing Mesh ទោះបីជាចូលតាម IP ណាក៏ដោយ ក៏អាចទទួលបានទំព័រកម្មវិធីបានយ៉ាងរលូន។

---

## ៤. បញ្ហាប្រឈម និងដំណោះស្រាយ (Challenges & Solutions)

| បញ្ហាប្រឈម (Challenges) | មូលហេតុ (Root Causes) | ដំណោះស្រាយ (Solutions) |
|---|---|---|
| **Worker Nodes មិនអាចទាញយក Image ពី ECR បាន** | ECR ជា Private Repository ហើយ Worker Nodes គ្មាន Auth Token | បន្ថែមទង់ `--with-registry-auth` នៅក្នុងពាក្យបញ្ជា `docker stack deploy` និងធ្វើ login ECR លើ Manager មុន deploy |
| **Jenkins Buildx Architecture Mismatch** | Jenkins ដំណើរការលើ ARM64 ប៉ុន្តែ EC2 Node ប្រើ AMD64 | បន្ថែមទង់ `--platform linux/amd64` នៅក្នុង `docker buildx build` |
| **Port Conflict នៅលើ EC2** | Port 80 អាចត្រូវបានប្រើប្រាស់ដោយ Web Server ផ្សេង | ប្តូរ Host Port ទៅ `8898:80` នៅក្នុង `docker-stack.yml` |
| **Downtime អំឡុងពេល Deploy ថ្មី** | Container ទាំងអស់ត្រូវបិទព្រមគ្នា | កំណត់ `order: start-first` និង `parallelism: 1` ក្នុង `update_config` |

---

## ៥. សេចក្តីសន្និដ្ឋាន (Conclusion)
ការអនុវត្តកិច្ចការផ្ទះ Homework 2 នេះបានបង្ហាញយ៉ាងច្បាស់អំពីអត្ថប្រយោជន៍ដ៏មហិមានៃ CI/CD Pipeline លើ Cloud Computing។ ការរួមបញ្ចូលគ្នារវាង GitHub Webhook, Jenkins Pipeline as Code, Amazon ECR និង Docker Swarm Rolling Update បានបង្កើតនូវប្រព័ន្ធដឹកជញ្ជូនកម្មវិធីមួយដែលមានលក្ខណៈស្វ័យប្រវត្តិ ឆាប់រហ័ស មានសុវត្ថិភាព និងគ្មាន Downtime ឡើយ។
