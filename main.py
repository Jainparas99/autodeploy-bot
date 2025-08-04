import sys
import argparse
from utils import parse_prompt, deployment_strategy, analyze_repository
from deployer import clone_repo, generate_terraform, run_terraform, extract_zip, apply_app_patches, deployment_config, setup_logger

def main():
    
    parser = argparse.ArgumentParser(description='Deploy applications automatically')
    parser.add_argument('prompt', help='Natural language deployment description')
    parser.add_argument('--repo', help='GitHub repository URL')
    parser.add_argument('--zip', help='Path to zip file')
    
    args = parser.parse_args()
    
    if not args.repo and not args.zip:
        print("Error: Either --repo or --zip must be provided")
        return
    
    # Logger
    logger = setup_logger()
    logger.info(f"Starting deployment process with prompt: {args.prompt}")
    
    try:
        deploy_application(args.prompt, args.repo, args.zip, logger)
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        print(f"Deployment failed: {str(e)}")

def deploy_application(prompt, repo_url=None, zip_path=None, logger=None):
    print(f"Parsing input: {prompt}")
    parsed = parse_prompt(prompt)
    logger.info(f"Parsed prompt - Cloud: {parsed['cloud']}, App: {parsed['app_type']}, Infra: {parsed['infra_type']}")
    
    # Code
    if repo_url:
        repo_path = clone_repo(repo_url)
        logger.info(f"Repository cloned to: {repo_path}")
    else:
        repo_path = extract_zip(zip_path)
        logger.info(f"Zip extracted to: {repo_path}")
    
    # Analyzing
    app_info = analyze_repository(repo_path)
    logger.info(f"Application analysis complete: {app_info}")
    

    strategy = deployment_strategy(app_info, parsed, repo_path)
    logger.info(f"Chosen deployment strategy: {strategy}")
    
    apply_app_patches(app_info, repo_path, logger)
    
    print("Generating infrastructure configuration...")
    template_name = deployment_config(
        parsed['cloud'] or 'aws', 
        deployment_strategy, 
        app_info, 
        repo_url or zip_path
    )
    
    generate_terraform(app_info, repo_url or zip_path, template_name)
    
    # Deploy
    print("Deploying infrastructure...")
    public_ip = run_terraform(logger)
    
    if public_ip:
        print(f"Deployment successful!")
        print(f"App is live at: http://{public_ip}:{app_info.get('port', 5000)}")
        logger.info(f"Deployment successful. App accessible at: http://{public_ip}:{app_info.get('port', 5000)}")
    else:
        print("Deployment failed.")
        logger.error("Deployment failed")

if __name__ == "__main__":
    main()