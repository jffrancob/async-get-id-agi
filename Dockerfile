# Use the official image as a parent image.
FROM python:3.8.2-alpine

# Git package install
RUN apk add git

# Copy the file from your host to your current location.
ADD app/ /usr/src/

# Set the working directory.
WORKDIR /usr/src/app

# Dependencies install
RUN pip install -r requirements.txt

# Inform Docker that the container is listening on the specified port at runtime.
EXPOSE 4573

# Run the application
CMD [ "python", "async-get-id.py" ]