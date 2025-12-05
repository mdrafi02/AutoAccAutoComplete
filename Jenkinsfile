pipeline {
    agent any
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code...'
                checkout scm
            }
        }
        
        stage('Build') {
            steps {
                echo 'Building Stage ...'
            }
        }
        
        stage('Test') {
            steps {
                echo 'Test Stage ...'
            }
        }
        
        stage('Deploy') {
            steps {
                echo 'Deploy Stage ...'
            }
        }
    }
}
