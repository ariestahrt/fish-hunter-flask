FROM python:3.8

WORKDIR /fish-hunter

COPY . /fish-hunter

# Adding trusting keys to apt for repositories
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -

# Adding Google Chrome to the repositories
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'

# update
RUN apt-get -y update

# install 7zip
RUN apt-get install -y p7zip-full

# install nano
RUN apt-get install -y nano

# install screen
RUN apt-get install -y screen

# install sudo
RUN apt-get install -y sudo

# Magic happens
RUN apt-get install -y google-chrome-stable

# Installing Unzip
RUN apt-get install -yqq unzip

# Download the Chrome Driver
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`\
curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE\
`/chromedriver_linux64.zip

# Unzip the Chrome Driver into /usr/local/bin directory
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

# Set display port as an environment variable
ENV DISPLAY=:99

# install dependencies
RUN python3 -m pip install -r requirements.txt

# install urllib3
RUN python3 -m pip install urllib3

EXPOSE 8080

CMD ["/bin/bash"]

# enable this if you want to run the app in the container
# CMD ["waitress-serve", "--call", "app:create_app"]