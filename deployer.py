import os
from git import Repo
import json
from jinja2 import Environment, FileSystemLoader
import shutil
import subprocess
import time

def clone_repo(repo_url, dest_folder="deployments/current_app"):
    if os.path.exists(dest_folder):
        os.system(f"rm -rf {dest_folder}")
    os.makedirs(dest_folder, exist_ok=True)
    Repo.clone_from(repo_url, dest_folder)
    return dest_folder

def extract_zip(zip_path, dest_folder="deployments/current_app"):
    import zipfile
    if os.path.exists(dest_folder):
        shutil.rmtree(dest_folder)
    os.makedirs(dest_folder, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(dest_folder)
    
    return dest_folder

def deployment_config(cloud, infra_type, app_info, repo_url):
    config_map = {
        "aws": {
            "vm": "aws_vm.tf.j2",
            "serverless": "aws_lambda.tf.j2", 
            "kubernetes": "aws_eks.tf.j2"
        },
        "gcp": {
            "vm": "gcp_vm.tf.j2",
            "serverless": "gcp_functions.tf.j2",
            "kubernetes": "gcp_gke.tf.j2"
        },
        "azure": {
            "vm": "azure_vm.tf.j2",
            "serverless": "azure_functions.tf.j2",
            "kubernetes": "azure_aks.tf.j2"
        }
    }
    
    template_name = config_map.get(cloud, {}).get(infra_type, "aws_vm.tf.j2")
    return template_name

def django_settings(repo_path, logger):    
    settings_files = []
    for root, dirs, files in os.walk(repo_path):
        if 'settings.py' in files:
            settings_files.append(os.path.join(root, 'settings.py'))
    
    for settings_file in settings_files:
        with open(settings_file, 'r') as f:
            content = f.read()
        
        if 'ALLOWED_HOSTS' not in content:
            content += '\nALLOWED_HOSTS = ["*"]\n'
        elif 'ALLOWED_HOSTS = []' in content:
            content = content.replace('ALLOWED_HOSTS = []', 'ALLOWED_HOSTS = ["*"]')
        
        if 'DEBUG = True' in content:
            content = content.replace('DEBUG = True', 'DEBUG = False')
        
        with open(settings_file, 'w') as f:
            f.write(content)
        
        logger.info(f"Patched Django settings: {settings_file}")

def node_app(repo_path, logger):
    
    package_json_path = None
    for root, dirs, files in os.walk(repo_path):
        if 'package.json' in files:
            package_json_path = os.path.join(root, 'package.json')
            break
    
    if package_json_path:
        with open(package_json_path, 'r') as f:
            package_data = json.load(f)
        
    
        if 'scripts' not in package_data:
            package_data['scripts'] = {}
        
        if 'start' not in package_data['scripts']:
            main_file = package_data.get('main', 'index.js')
            package_data['scripts']['start'] = f"node {main_file}"
        
        with open(package_json_path, 'w') as f:
            json.dump(package_data, f, indent=2)
        
        logger.info("Patched Node.js package.json")

def flask_binds(repo_path):
    for file in ["app.py", "main.py"]:
        path = os.path.join(repo_path, file)
        if os.path.exists(path):
            with open(path, "r") as f:
                code = f.read()
            if "app.run(" in code and "host=" not in code:
                updated = code.replace("app.run(", "app.run(host='0.0.0.0', ")
                with open(path, "w") as f:
                    f.write(updated)
                print(f"Patched {file} to bind to host")

def apply_app_patches(app_info, repo_path, logger):

    if app_info['framework'] == 'flask':
        flask_binds(repo_path)
        logger.info("Applied Flask host binding patch")
    
    elif app_info['framework'] == 'django':
        django_settings(repo_path, logger)
    
    elif app_info['framework'] == 'node':
        node_app(repo_path, logger)

def generate_terraform(app_info, repo_url, template_name="aws_vm.tf.j2", output_dir="deployments/tf_generated"):
   # i have kept the template name as aws_vm.tf.j2 because it is the default template for aws vm but we can add other templates too.
   os.makedirs(output_dir, exist_ok=True)

   env = Environment(loader=FileSystemLoader("terraform_templates"))
   template = env.get_template(template_name)

   rendered = template.render(
       repo_url=repo_url,
       start_command=app_info["start_command"],
       port=app_info.get("port", 5000),
       app_type=app_info.get("framework"),
       language=app_info.get("language")
   )

   with open(os.path.join(output_dir, "main.tf"), "w") as f:
       f.write(rendered)


   cloud_provider = template_name.split('_')[0] 
   
   variables_content = get_variables_for_cloud(cloud_provider)
   
   with open(os.path.join(output_dir, "variables.tf"), "w") as f:
       f.write(variables_content)

   print(f"Terraform files generated at: {output_dir}")

def get_variables_for_cloud(cloud_provider):
   variables = {
       "aws": """\
variable "aws_access_key" {}
variable "aws_secret_key" {}
variable "ami_id" {}
variable "key_name" {}
variable "private_key_path" {}
""",
       "gcp": """\
variable "project_id" {}
variable "credentials_file" {}
variable "region" {}
variable "zone" {}
""",
       "azure": """\
variable "subscription_id" {}
variable "client_id" {}
variable "client_secret" {}
variable "tenant_id" {}
variable "resource_group_name" {}
"""
   }
   return variables.get(cloud_provider, variables["aws"])

def run_terraform(logger, terraform_dir="deployments/tf_generated"):
    
    logger.info("Initializing Terraform...")
    init_result = subprocess.run(
        ["terraform", "init"], 
        cwd=terraform_dir, 
        capture_output=True, 
        text=True
    )
    
    logger.info("Terraform init output: " + init_result.stdout)
    if init_result.returncode != 0:
        logger.error("Terraform init failed: " + init_result.stderr)
        return None
    
    logger.info("Applying Terraform configuration...")
    apply_result = subprocess.run(
        ["terraform", "apply", "-auto-approve"], 
        cwd=terraform_dir, 
        capture_output=True, 
        text=True
    )
    
    logger.info("Terraform apply output: " + apply_result.stdout)
    if apply_result.returncode != 0:
        logger.error("Terraform apply failed: " + apply_result.stderr)
        return None
    
    output_result = subprocess.run(
        ["terraform", "output", "-json"], 
        cwd=terraform_dir, 
        capture_output=True, 
        text=True
    )
    
    try:
        outputs = json.loads(output_result.stdout)
        public_ip = outputs["public_ip"]["value"]
        logger.info(f"Infrastructure provisioned successfully. Public IP: {public_ip}")
        return public_ip
    except Exception as e:
        logger.error(f"Failed to extract Terraform outputs: {e}")
        return None

def setup_logger():
    import logging
    # make log 
    os.makedirs("logs", exist_ok=True)
    
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"logs/deployment_{int(time.time())}.log"),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)