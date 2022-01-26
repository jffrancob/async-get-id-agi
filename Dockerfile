# Building stage
FROM python:3.5

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /etc/getid/
COPY ./config.yaml /etc/getid/config.yaml

# set the working directory in the container
WORKDIR /app

# copy the content of the local src directory to the working directory
COPY ./src/ .

# command to run on container start
#CMD [ "python", "./server.py" ]
ENTRYPOINT python server.py
