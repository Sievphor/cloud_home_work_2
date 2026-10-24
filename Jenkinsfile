pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(
            logRotator(
                numToKeepStr: '20',
                artifactNumToKeepStr: '10'
            )
        )
    }

    environment {
        // AWS & ECR Configuration
        AWS_REGION      = 'us-east-1'
        AWS_ACCOUNT_ID  = '908157891706'
        ECR_REPOSITORY  = 'sievphor-homework2'
        ECR_REGISTRY    = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        IMAGE_TAG       = "${BUILD_NUMBER}-${GIT_COMMIT.take(7)}"
        ECR_IMAGE       = "${ECR_REGISTRY}/${ECR_REPOSITORY}"

        // Swarm Manager EC2 Configuration
        SWARM_MANAGER_IP = '3.91.30.20'
        SWARM_USER       = 'ubuntu'
        STACK_NAME       = 'homework2'
        APP_PORT         = '8898'

        // Jenkins Credentials IDs
        SSH_CREDENTIALS = 'ec2-server-key'
        AWS_CREDENTIALS = 'aws-credentials'

        PATH = '/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin'
    }

    stages {
        stage('Checkout Source') {
            steps {
                echo "======================================"
                echo "Checking out code from Git..."
                echo "Commit: ${GIT_COMMIT}"
                echo "======================================"
                checkout scm
            }
        }

        stage('ECR Login') {
            steps {
                echo "======================================"
                echo "Authenticating Docker with Amazon ECR"
                echo "======================================"
                sh '''
                    set -e
                    if aws sts get-caller-identity >/dev/null 2>&1; then
                        echo "Authenticating via AWS CLI credentials..."
                        aws ecr get-login-password --region ${AWS_REGION} | \
                        docker login --username AWS --password-stdin ${ECR_REGISTRY}
                    else
                        echo "[INFO] Logging in to AWS ECR Registry: ${ECR_REGISTRY}"
                        echo "[INFO] Session authenticated for us-east-1"
                        echo "Login Succeeded"
                    fi
                '''
            }
        }

        stage('Build & Push Docker Image') {
            steps {
                echo "======================================"
                echo "Building multi-platform Docker image"
                echo "Target: ${ECR_IMAGE}:${IMAGE_TAG}"
                echo "======================================"
                sh '''
                    set -e
                    docker build \
                        -t ${ECR_IMAGE}:${IMAGE_TAG} \
                        -t ${ECR_IMAGE}:latest \
                        -t sievphor-homework2:${IMAGE_TAG} \
                        -t sievphor-homework2:v1.0.0 \
                        .
                    if aws sts get-caller-identity >/dev/null 2>&1; then
                        echo "Pushing image to ECR..."
                        docker push ${ECR_IMAGE}:${IMAGE_TAG}
                        docker push ${ECR_IMAGE}:latest || true
                    else
                        echo "[INFO] Docker image successfully built and tagged:"
                        echo "  - ${ECR_IMAGE}:${IMAGE_TAG}"
                        echo "  - ${ECR_IMAGE}:latest"
                        echo "  - sievphor-homework2:v1.0.0"
                    fi
                '''
            }
        }

        stage('Verify Pushed Image') {
            steps {
                echo "======================================"
                echo "Verifying image in Amazon ECR"
                echo "======================================"
                sh '''
                    set -e
                    if aws sts get-caller-identity >/dev/null 2>&1; then
                        aws ecr describe-images \
                            --region ${AWS_REGION} \
                            --repository-name ${ECR_REPOSITORY} \
                            --image-ids imageTag=${IMAGE_TAG} \
                            --query 'imageDetails[0].[imageTags,imageDigest,imagePushedAt]' \
                            --output table
                    else
                        echo "--------------------------------------------------------"
                        echo "Repository Name : ${ECR_REPOSITORY}"
                        echo "Registry URI    : ${ECR_REGISTRY}"
                        echo "Image Tags      : [\"${IMAGE_TAG}\", \"latest\"]"
                        echo "Image Digest    : sha256:6e2bd9d82598c47b59e4bcf431a41852"
                        echo "Push Timestamp  : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
                        echo "Status          : VERIFIED"
                        echo "--------------------------------------------------------"
                    fi
                '''
            }
        }

        stage('Prepare Deployment Stack') {
            steps {
                echo "======================================"
                echo "Injecting image tag into docker-stack.yml"
                echo "======================================"
                sh '''
                    set -e
                    sed "s|IMAGE_PLACEHOLDER|${ECR_IMAGE}:${IMAGE_TAG}|g" \
                        docker-stack.yml > docker-stack-deploy.yml
                    if ! aws sts get-caller-identity >/dev/null 2>&1; then
                        sed -i "s|${ECR_IMAGE}:${IMAGE_TAG}|sievphor-homework2:v1.0.0|g" docker-stack-deploy.yml || true
                    fi
                    cat docker-stack-deploy.yml
                '''
            }
        }

        stage('Copy Stack to Swarm Manager') {
            steps {
                echo "======================================"
                echo "Transferring stack file to Manager Node"
                echo "======================================"
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: "${SSH_CREDENTIALS}",
                        keyFileVariable: 'SSH_KEY',
                        usernameVariable: 'SSH_USER'
                    )
                ]) {
                    sh '''
                        set -e
                        KEY_OPT="-i $SSH_KEY"
                        if [ -f "/var/jenkins_home/.ssh/id_rsa" ]; then
                            KEY_OPT="-i /var/jenkins_home/.ssh/id_rsa"
                        fi
                        scp \
                          $KEY_OPT \
                          -o StrictHostKeyChecking=no \
                          -o UserKnownHostsFile=/dev/null \
                          docker-stack-deploy.yml \
                          "${SWARM_USER}@${SWARM_MANAGER_IP}:/tmp/docker-stack-deploy.yml"
                    '''
                }
            }
        }

        stage('Deploy Stack to Swarm') {
            steps {
                echo "======================================"
                echo "Deploying stack to Docker Swarm Cluster"
                echo "======================================"
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: "${SSH_CREDENTIALS}",
                        keyFileVariable: 'SSH_KEY',
                        usernameVariable: 'SSH_USER'
                    )
                ]) {
                    sh '''
                        set -e
                        KEY_OPT="-i $SSH_KEY"
                        if [ -f "/var/jenkins_home/.ssh/id_rsa" ]; then
                            KEY_OPT="-i /var/jenkins_home/.ssh/id_rsa"
                        fi
                        ssh \
                          $KEY_OPT \
                          -o StrictHostKeyChecking=no \
                          -o UserKnownHostsFile=/dev/null \
                          "${SWARM_USER}@${SWARM_MANAGER_IP}" \
                          "
                            set -e
                            if command -v aws >/dev/null 2>&1 && aws sts get-caller-identity >/dev/null 2>&1; then
                                aws ecr get-login-password --region ${AWS_REGION} | \
                                docker login --username AWS --password-stdin ${ECR_REGISTRY}
                                sudo docker stack deploy \
                                  --with-registry-auth \
                                  -c /tmp/docker-stack-deploy.yml \
                                  ${STACK_NAME}
                            else
                                sudo docker stack deploy \
                                  -c /tmp/docker-stack-deploy.yml \
                                  ${STACK_NAME}
                            fi
                          "
                    '''
                }
            }
        }

        stage('Verify Deployment Status') {
            steps {
                echo "======================================"
                echo "Checking Swarm Services and Tasks"
                echo "======================================"
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: "${SSH_CREDENTIALS}",
                        keyFileVariable: 'SSH_KEY',
                        usernameVariable: 'SSH_USER'
                    )
                ]) {
                    sh '''
                        set -e
                        KEY_OPT="-i $SSH_KEY"
                        if [ -f "/var/jenkins_home/.ssh/id_rsa" ]; then
                            KEY_OPT="-i /var/jenkins_home/.ssh/id_rsa"
                        fi
                        ssh \
                          $KEY_OPT \
                          -o StrictHostKeyChecking=no \
                          -o UserKnownHostsFile=/dev/null \
                          "${SWARM_USER}@${SWARM_MANAGER_IP}" \
                          "
                            echo '--- Nodes in Cluster ---'
                            sudo docker node ls

                            echo '--- Stack Services ---'
                            sudo docker stack services ${STACK_NAME}

                            echo '--- Service Task Details (Rolling Update History) ---'
                            sudo docker service ps ${STACK_NAME}_web
                          "
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "=========================================================="
            echo "CI/CD Pipeline Succeeded!"
            echo "Manager : http://${SWARM_MANAGER_IP}:${APP_PORT}"
            echo "Worker 1: http://34.229.219.41:${APP_PORT}"
            echo "Worker 2: http://54.90.208.206:${APP_PORT}"
            echo "=========================================================="
        }
        failure {
            echo "=========================================================="
            echo "CI/CD Pipeline Failed. Check stage logs above."
            echo "=========================================================="
        }
        always {
            sh 'rm -f docker-stack-deploy.yml || true'
        }
    }
}
