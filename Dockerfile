# Use the official image as a parent image.
FROM python:3.8.2-alpine
#FROM python:2.7

# Git package install
RUN apk add git gcc musl-dev

# Copy the file from your host to your current location.
COPY app /usr/src/app

# Set the working directory.
WORKDIR /usr/src/app

# pip update
RUN pip install --upgrade pip

# Dependencies install
RUN pip install -r requirements.txt

# Inform Docker that the container is listening on the specified port at runtime.
EXPOSE 4573

# Run the application
CMD [ "python", "async-get-id.py" ]
