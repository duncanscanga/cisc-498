# Auto-Grader for the Engineering Dept. at Queen's


# Setting up local development environment
pip install -r requirements.txt

python -m app


# Deploying with Docker
docker build --tag=dscanga/cisc498:v1 .   

docker run -p 8081:8081 dscanga/cisc498:v1 python3 -m app

