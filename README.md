# Autodeploy Bot

This is my submission for the test.
This project automates infrastructure provisioning and remote deployment using Terraform and shell scripts.

---

## Features

- Provision EC2 instances using Terraform
- SSH key-based authentication
- Remote provisioning with shell scripts
- Dynamic environment setup
- Clean separation of infrastructure and app logic

---

## Project Structure

autodeploy-bot/
deployments/              # Terraform configurations
    main.tf
    variables.tf   
scripts/                  # Shell scripts for remote execution
    deploy.sh
    .gitignore
    requirement.txt          # Python dependencies (if any)
    README.md

## Setup Instructions

### 1. Clone the repository

git clone https://github.com/Jainparas99/autodeploy-bot.git
cd autodeploy-bot

### 2. Create a virtual environment

python3 -m venv .venv
source .venv/bin/activate  

### 3. Install Python dependencies

pip install -r requirement.txt

### 4. Configure AWS credentials

Make sure you’ve set your AWS credentials either in ~/.aws/credentials or by exporting them:

export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key

---

## Terraform Deployment

### Initialize Terraform

cd deployments
terraform init

### Apply configuration

terraform apply

This will provision the infrastructure and run remote scripts as defined in your provisioners.

---

## Example USAGE 

python3 main.py "Deploy this flask app on AWS" --repo https://github.com/Arvo-AI/hello_world

## Sample Terraform Variable File (terraform.tfvars)

aws_access_key = "YOUR_ACCESS_KEY"
aws_secret_key = "YOUR_SECRET_KEY"
key_name       = "your-ec2-keypair-name"
private_key_path = "/key path"
ami_id         = "ami-xxxxxxxxxxxxxxxxx"

## Author

Paras Jain  
GitHub: https://github.com/Jainparas99
