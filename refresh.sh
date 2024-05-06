#!/bin/sh

# Set the URL to send the POST request
URL="http://localhost:5000/api/update"

curl -X POST $URL
