# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the image name
LABEL maintainer="Sanyam Malik"
LABEL description="Codebase-flask App"
LABEL version="3.0"
LABEL image_name="codebase-flask"
LABEL tag="latest"

# Install git and cron
RUN apt-get update && apt-get install -y git cron curl nano

# Set the working directory in the container
WORKDIR /codebase-flask

# Copy the current directory contents into the container at /codebase-flask
COPY . /codebase-flask

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port available as specified by the PORT environment variable or default to 5000
ENV PORT=5000
EXPOSE $PORT

# Create cron log file
RUN touch /var/log/cron.log

# Make the script executable
RUN chmod +x /codebase-flask/refresh.sh

# Add cron job command to the system-wide cron directory
RUN echo "*/10 * * * * root /codebase-flask/refresh.sh >> /var/log/cron.log 2>&1" >> /etc/cron.d/crontab

# Start cron service in the background and tail the log file
RUN cron

# Define environment variables
ENV AUTO_UPDATE="false"
ENV DATABASE_NAME="codebase"
ENV GIT_URL="https://github.com/Sanyam-malik/Codebase.git"
ENV DEST_PATH="codebase"
ENV BRANCH_NAME="new-journey"
ENV ACCESS_TOKEN=""
ENV UPDATE_URL="https://github.com/Sanyam-malik/Codebase-Flask.git"
ENV UPDATE_BRANCH="main"
ENV UPDATE_ACCESS_TOKEN=""
ENV SMTP_ENABLE="false"
ENV SMTP_ADDRESS=""
ENV SMTP_PORT=""
ENV SMTP_USERNAME=""
ENV SMTP_PASSWORD=""
ENV RECIPIENT_EMAIL=""
ENV EXTERNAL_URL=""

# Start cron service and Flask application concurrently
CMD cron -f & python run.py
