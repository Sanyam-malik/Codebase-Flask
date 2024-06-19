import json
import logging
import os

import yaml

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)


def generate_gateway_config():
    gateway_port = os.getenv('PORT', '5000')
    core_port = str(int(gateway_port)+50)
    marketplace_port = str(int(gateway_port) + 100)
    integration_port = str(int(gateway_port) + 150)

    gateway_config = {
        "instance-name": "Default Datacenter",
        "default": f"http://localhost:{gateway_port}/cb",
        "services": [
            {
                "name": "Codebase - Core",
                "base_url": "/cb",
                "service_url": f"http://localhost:{core_port}"
            },
            {
                "name": "Codebase - Marketplace",
                "base_url": "/marketplace",
                "service_url": f"http://localhost:{marketplace_port}"
            },
            {
                "name": "Codebase - Integrations",
                "base_url": "/integration",
                "service_url": f"http://localhost:{integration_port}"
            }
        ]
    }

    with open('gateway-config.json', 'w') as json_file:
        json.dump(gateway_config, json_file, indent=4)
    logging.info("Gateway Config generated successfully...")


def generate_config_yaml():
    config_yaml = {
        'PORT': os.getenv('PORT', '5000'),
        'ACCESS_TOKEN': os.getenv('ACCESS_TOKEN', ''),
        'BRANCH_NAME': os.getenv('BRANCH_NAME', 'new-journey'),
        'DATABASE_NAME': os.getenv('DATABASE_NAME', 'codebase'),
        'DEST_PATH': os.getenv('DEST_PATH', 'codebase'),
        'EXTERNAL_URL': os.getenv('EXTERNAL_URL', ''),
        'GIT_URL': os.getenv('GIT_URL', 'https://github.com/Sanyam-malik/Codebase'),
        'RECIPIENT_EMAIL': os.getenv('RECIPIENT_EMAIL', ''),
        'SMTP_ADDRESS': os.getenv('SMTP_ADDRESS', 'smtp.gmail.com'),
        'SMTP_ENABLE': os.getenv('SMTP_ENABLE', 'true'),
        'SMTP_PASSWORD': os.getenv('SMTP_PASSWORD', ''),
        'SMTP_PORT': os.getenv('SMTP_PORT', '587'),
        'SMTP_USERNAME': os.getenv('SMTP_USERNAME', ''),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
        'YOUTUBE_API_KEY': os.getenv('YOUTUBE_API_KEY', '')
    }

    with open('config.yaml', 'w') as yaml_file:
        yaml.dump(config_yaml, yaml_file, default_flow_style=False)
    logging.info("Application Config generated successfully...")


if __name__ == "__main__":
    generate_config_yaml()
    generate_gateway_config()
