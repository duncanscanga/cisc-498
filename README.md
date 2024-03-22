# Auto-Grader for the Engineering Dept. at Queen's

# View Demo


# Setting up local development environment
pip install -r requirements.txt

python -m app


# Deploying with Docker

To Update Image:
docker build --tag=dscanga/cisc498:v1 .   

To Get Latest Image: 
docker pull dscanga/cisc498:v1

To Run:
docker run -p 8081:8081 dscanga/cisc498:v1 python3 -m app
