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
        SWARM_MANAGER_IP = '13.220.98.249'
        SWARM_USER       = 'ubuntu'
        STACK_NAME       = 'homework2'
        APP_PORT         = '8898'

        // Jenkins Credentials IDs
        SSH_CREDENTIALS = 'swarm-ssh-key'
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
                    aws ecr get-login-password --region ${AWS_REGION} | \
                    docker login --username AWS --password-stdin ${ECR_REGISTRY}
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
                    docker buildx build \
                        --platform linux/amd64 \
                        -t ${ECR_IMAGE}:${IMAGE_TAG} \
                        -t ${ECR_IMAGE}:latest \
                        --push .
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
                    aws ecr describe-images \
                        --region ${AWS_REGION} \
                        --repository-name ${ECR_REPOSITORY} \
                        --image-ids imageTag=${IMAGE_TAG} \
                        --query 'imageDetails[0].[imageTags,imageDigest,imagePushedAt]' \
                        --output table
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
                        scp \
                          -i "$SSH_KEY" \
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
                        ssh \
                          -i "$SSH_KEY" \
                          -o StrictHostKeyChecking=no \
                          -o UserKnownHostsFile=/dev/null \
                          "${SWARM_USER}@${SWARM_MANAGER_IP}" \
                          "
                            set -e
                            # Re-login to ECR on Swarm Manager for private pull authorization
                            aws ecr get-login-password --region ${AWS_REGION} | \
                            docker login --username AWS --password-stdin ${ECR_REGISTRY}

                            sudo docker stack deploy \
                              --with-registry-auth \
                              -c /tmp/docker-stack-deploy.yml \
                              ${STACK_NAME}
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
                        ssh \
                          -i "$SSH_KEY" \
                          -o StrictHostKeyChecking=no \
                          -o UserKnownHostsFile=/dev/null \
                          "${SWARM_USER}@${SWARM_MANAGER_IP}" \
                          "
                            echo '--- Nodes in Cluster ---'
                            docker node ls

                            echo '--- Stack Services ---'
                            docker stack services ${STACK_NAME}

                            echo '--- Service Task Details (Rolling Update History) ---'
                            docker service ps ${STACK_NAME}_web
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
