# Auto-Grader for the Engineering Dept. at Queen's

# View Demo
https://drive.google.com/file/d/1-yHxt_qN67OIznzGnJ_7px42LnyH786x/view?usp=drive_link

# Setting up local development environment
pip install -r requirements.txt

python -m app


# Deploying with Docker

To Update Image:
docker build --tag=dscanga/cisc498:v1 .   
docker push dscanga/cisc498:v1

To Get Latest Image: 
docker pull dscanga/cisc498:v1

To Run:
docker run -p 8081:8081 dscanga/cisc498:v1 python3 -m app


