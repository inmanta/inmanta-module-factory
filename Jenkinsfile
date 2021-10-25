pipeline {
    agent any
    triggers {
        cron(BRANCH_NAME == 'master' ? 'H H(2-5) * * *' : '')
    }

    environment {
        REPO_NAME = 'inmanta-module-factory'
        PIP_INDEX_URL = 'https://artifacts.internal.inmanta.com/inmanta/dev'
        PIP_PRE = 'true'
    }

    options {
        disableConcurrentBuilds()
        checkoutToSubdirectory(env.REPO_NAME)
        skipDefaultCheckout()
        buildDiscarder(logRotator(numToKeepStr: '30'))
    }

    stages {
        stage('Setup') {
          steps {
            deleteDir()
            dir(env.REPO_NAME) {
              sh '''
                rm -rf ${WORKSPACE}/env
                python3 -m venv ${WORKSPACE}/env
                . ${WORKSPACE}/env/bin/activate
                make install
              '''
            }
          }
        }

        stage('Tests') {
          steps {
            dir(env.REPO_NAME) {
              sh '''
                . ${WORKSPACE}/env/bin/activate
                pytest \
                  --junitxml=junit.xml \
                  --log-cli-level DEBUG \
                  --basetemp=${WORKSPACE}/tmp \
                  -s -vvv \
                  tests
              '''
            }
            junit "${env.REPO_NAME}/junit.xml"
          }
        }

        stage('Code linting') {
          steps {
            dir(env.REPO_NAME) {
              sh'''
                . ${WORKSPACE}/env/bin/activate
                make pep8
              '''
            }
          }
        }

        stage('Code static typing check') {
          steps {
            dir(env.REPO_NAME) {
              sh'''
                . ${WORKSPACE}/env/bin/activate
                make mypy
              '''
            }
          }
        }

        stage('Publish to devpi') {
          when {
            expression { BRANCH_NAME == 'master' }
          }
          steps {
            withCredentials([
              usernamePassword(
                credentialsId: 'devpi-user',
                passwordVariable: 'DEVPI_PASS',
                usernameVariable: 'DEVPI_USER'
              )
            ]) {
              dir(env.REPO_NAME) {
                sh '''
                  ${WORKSPACE}/env/bin/pip3 install -U devpi-client
                  ${WORKSPACE}/env/bin/devpi use https://artifacts.internal.inmanta.com/inmanta/dev
                  ${WORKSPACE}/env/bin/devpi login ${DEVPI_USER} --password=${DEVPI_PASS}
                  rm -f dist/*

                  ${WORKSPACE}/env/bin/python3 -m pep517.build --source .

                  ${WORKSPACE}/env/bin/devpi upload dist/*.dev*
                  ${WORKSPACE}/env/bin/devpi logoff
                 '''
              }
            }
          }
        }
    }

    // post {
    //   always {
    //     deleteDir()
    //   }
    // }
}
