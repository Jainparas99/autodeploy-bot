import re
import os
import json

def parse_prompt(prompt):
    prompt = prompt.lower()
    result = {
        "cloud": None,
        "app_type": None,
        "infra_type": None 
    }
    # Find the cloud
    if "aws" in prompt:
        result["cloud"] = "aws"
    elif "gcp" in prompt:
        result["cloud"] = "gcp"
    elif "azure" in prompt:
        result["cloud"] = "azure"

    # Find the app
    if "flask" in prompt:
        result["app_type"] = "flask"
    elif "django" in prompt:
        result["app_type"] = "django"
    elif "node" in prompt or "express" in prompt:
        result["app_type"] = "node"
    elif "static" in prompt:
        result["app_type"] = "static"

    # Find Infra
    if "kubernetes" in prompt:
        result["infra_type"] = "kubernetes"
    elif "serverless" in prompt:
        result["infra_type"] = "serverless"
    elif "vm" in prompt or "ec2" in prompt:
        result["infra_type"] = "vm"

    return result
    
def static_site(repo_path):
    static_indicators = ["index.html", "index.htm"]
    build_indicators = ["dist", "build", "public"]
    
    files = os.listdir(repo_path)
    
    # Check for direct static files
    if any(indicator in files for indicator in static_indicators):
        return {"is_static": True, "root_dir": repo_path}
    
    # Check for build directories
    for build_dir in build_indicators:
        build_path = os.path.join(repo_path, build_dir)
        if os.path.exists(build_path):
            build_files = os.listdir(build_path)
            if any(indicator in build_files for indicator in static_indicators):
                return {"is_static": True, "root_dir": build_path}
    
    return {"is_static": False}

def analyze_repository(repo_path):
    app_info = {
        "language": None,
        "framework": None,
        "dependencies": [],
        "start_command": None,
        "port": None,
        "entry_file": None
    }

    app_subdir = None
    if os.path.exists(os.path.join(repo_path, "app")):
        app_subdir = "app"
    elif os.path.exists(os.path.join(repo_path, "src")):
        app_subdir = "src"
    
    search_path = os.path.join(repo_path, app_subdir) if app_subdir else repo_path
    files = os.listdir(search_path)

    # Detect Python
    if "requirements.txt" in files:
        app_info["language"] = "python"
        with open(os.path.join(search_path, "requirements.txt")) as f:
            deps = f.read().lower()
            app_info["dependencies"] = deps.splitlines()

            if "flask" in deps:
                app_info["framework"] = "flask"
                app_info["port"] = 5000
            elif "django" in deps:
                app_info["framework"] = "django"
                app_info["port"] = 8000

    # Detect Node.js
    elif "package.json" in files:
        app_info["language"] = "node"
        app_info["framework"] = "node"
        with open(os.path.join(search_path, "package.json")) as f:
            package = json.load(f)
            deps = package.get("dependencies", {})
            app_info["dependencies"] = list(deps.keys())
            scripts = package.get("scripts", {})
            app_info["start_command"] = scripts.get("start", "node index.js")
            app_info["entry_file"] = "index.js"

    # Find entry file
    for file in files:
        if file in ["app.py", "main.py"] and app_info["language"] == "python":
            app_info["entry_file"] = file
            if app_info["start_command"] is None:
                
                if app_subdir:
                    app_info["start_command"] = f"cd {app_subdir} && python {file}"
                else:
                    app_info["start_command"] = f"python {file}"
        elif file == "index.js" and app_info["language"] == "node":
            app_info["entry_file"] = "index.js"
            if app_info["start_command"] is None:
                if app_subdir:
                    app_info["start_command"] = f"cd {app_subdir} && node index.js"
                else:
                    app_info["start_command"] = f"node index.js"

    return app_info

def django_settings(repo_path):
    django_info = {"is_django": False, "settings_module": None, "wsgi_file": None}
    
    for root, dirs, files in os.walk(repo_path):
        if "settings.py" in files:
            django_info["is_django"] = True
            # Extract project name from path
            project_name = os.path.basename(root)
            django_info["settings_module"] = f"{project_name}.settings"
        if "wsgi.py" in files:
            django_info["wsgi_file"] = os.path.join(root, "wsgi.py")
    
    return django_info

def deployment_strategy(app_info, parsed_prompt, repo_path):

    if parsed_prompt["infra_type"]:
        return parsed_prompt["infra_type"]
    

    if app_info["framework"] == "flask" and len(app_info["dependencies"]) < 5:
        return "serverless" 
    
    elif app_info["framework"] == "django":
        return "vm"  
    
    elif "express" in app_info.get("dependencies", []):
        return "serverless"  
    
    elif os.path.exists(os.path.join(repo_path, "Dockerfile")):
        return "kubernetes"  
    
    else:
        return "vm" 