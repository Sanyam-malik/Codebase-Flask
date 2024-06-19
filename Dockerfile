# Use an official Python runtime based on Alpine as a parent image
FROM python:3.9-alpine

# Set the image name and labels
LABEL maintainer="Sanyam Malik"
LABEL description="Codebase-Flask"
LABEL version="3.0"
LABEL image_name="codebase-flask"
LABEL tag="latest"

# Install git, cron, and other dependencies including Java 17 and C++ compiler
RUN apk update && \
    apk add --no-cache git curl nano bash redis \
    openjdk17 \
    g++

# Set the working directory
WORKDIR /app

# Copy the entire current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set the PYTHONPATH to include the shared directory
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Create cron log file for both apps
RUN touch /var/log/cron.log

# Make the script executable
RUN chmod +x /app/refresh.sh

# Add cron job command to the system-wide cron directory for both apps
RUN echo "*/10 * * * * /app/refresh.sh >> /var/log/cron.log 2>&1" >> /etc/crontabs/root

# Copy entrypoint script
RUN chmod +x /app/entrypoint.sh

# Start cron service and both Flask applications concurrently
CMD ["/app/entrypoint.sh"]
