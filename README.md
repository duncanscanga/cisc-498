# Auto-Grader for the Engineering Dept. at Queen's University

Welcome to the GitHub repository for the Auto-Grader project, a powerful tool designed to automate the grading process for programming assignments in the Engineering Department at Queen's University. This tool supports the evaluation of code submissions, providing immediate feedback, test results, and plagiarism detection to enhance the learning and teaching experience.

## Features

The Auto-Grader offers a suite of features tailored to the needs of instructors and students alike:

- **User Authentication & Management:** Securely manage user sessions with distinct roles for students, TAs, and instructors.
- **Assignment Creation & Management:** Easily create and configure assignments with custom test cases and grading criteria.
- **Code Submission & Evaluation:** Students can submit their code directly through the platform, receiving instant feedback on test case outcomes.
- **Plagiarism Detection:** Integration with Moss to ensure academic integrity by detecting similar code submissions.
- **Feedback & Grading:** Detailed feedback and grading reports are generated for each submission, highlighting areas of improvement.

## View Demo

For a quick overview of what the Auto-Grader is capable of, check out our [demo video](https://drive.google.com/file/d/1-yHxt_qN67OIznzGnJ_7px42LnyH786x/view?usp=drive_link).

## Getting Started

Before diving in, please visit our [Wiki](https://github.com/duncanscanga/cisc-498/wiki) for comprehensive documentation on setting up, using, and troubleshooting the Auto-Grader.

### Setting Up Local Development Environment

To set up the Auto-Grader on your local machine, follow these steps:

```bash
pip install -r requirements.txt
python -m app
```

## Deploying with Docker

Docker simplifies deployment by containerizing the application. Here's how you can deploy the Auto-Grader using Docker:

### Update Image

To build and tag a new version of the Docker image, run:

```bash
docker build --tag=dscanga/cisc498:v1 .
docker push dscanga/cisc498:v1
```

### Get Latest Image

To pull the latest version of the Docker image, use:

```bash
docker pull dscanga/cisc498:v1
```

### Run the Container

To run the application using Docker, execute:

```bash
docker run -p <YourPort>:8081 dscanga/cisc498:v1 python3 -m app
```
Replace <YourPort> with the port number you wish to use for accessing the application. Ensure this port is open on your system or server.


## Licence
This project is licensed under the MIT License - see the LICENSE file for details.
