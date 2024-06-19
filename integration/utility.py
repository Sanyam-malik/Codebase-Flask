import json
import logging
import os
import random
import re
import shutil
import requests
import yaml

# Configure the logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)


def create_slug(input_string):
    # Convert the string to lowercase and replace spaces with hyphens
    slug = input_string.lower().replace(' ', '-')
    # Remove any characters that are not alphanumeric or hyphens
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'\-+', '-', slug)
    # Remove leading and trailing hyphens
    slug = slug.strip('-')
    return slug
