

\# NutriTrack

\## Intelligent Malnutrition Analysis and Early Risk Identification System



\### Project Overview

NutriTrack is a web-based nutritional screening prototype that records assessment information, calculates BMI, and identifies nutritional factors requiring further review.



\### Technologies Used

\- Python

\- Flask

\- SQLite

\- HTML, CSS and JavaScript

\- Docker

\- Git and GitHub

\- GitHub Actions



\### Run Locally Using Docker



Build the Docker image:



```bash

docker build -t nutritrack .

```



Start the application:



```bash

docker run -d --name nutritrack\_app -p 5000:5000 -v "%cd%\\data:/app/data" nutritrack

```



Open in your browser:



http://127.0.0.1:5000



\### CI Pipeline

GitHub Actions automatically performs these steps when code is pushed to the main branch:



1\. Checkout repository

2\. Set up Python 3.11

3\. Install dependencies

4\. Run automated nutritional screening tests

5\. Build Docker image



\### Repository

https://github.com/chinmai018/NutriTrack



\### Note

This project is an educational prototype. Its nutritional screening results are preliminary and are not a medical diagnosis.



