#!/bin/sh

# Set the URL to send the POST request
URL="http://localhost:5000/cb/api/update"

curl -X POST $URL
