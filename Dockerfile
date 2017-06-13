FROM python:2
MAINTAINER Benjamin Bouvier <public@benj.me>

# Setup layout.
RUN useradd -d /home/user -m -s /bin/bash -U user

# Install OS dependencies.
RUN apt-get update && \
    apt-get install -y git python python-dev libffi-dev \
    libxml2-dev libxslt-dev libyaml-dev libtiff-dev libjpeg-dev zlib1g-dev \
    libfreetype6-dev libwebp-dev build-essential gcc g++ wget;

# Install latest pip and python dependencies.
RUN cd /tmp && \
    wget https://bootstrap.pypa.io/get-pip.py && \
    python ./get-pip.py && \
    pip install -U setuptools && \
    pip install html2text simplejson BeautifulSoup

# Install node.js.
RUN curl -sL https://deb.nodesource.com/setup_8.x | bash - \
    && apt-get install -y nodejs

# Install weboob's code itself.
RUN git clone https://git.weboob.org/weboob/devel /home/user/weboob \
    && cd /home/user/weboob \
    && python ./setup.py install

RUN mkdir -p /flatisfy/data
VOLUME /flatisfy

# Install Flatisfy.
RUN cd /home/user \
    && git clone https://git.phyks.me/bnjbvr/flatisfy/ ./app \
    && cd ./app \
    && pip install -r requirements.txt \
    && npm install \
    && npm run build:prod

RUN chown user:user -R /home/user

COPY ./docker_run.sh /home/user/run.sh
RUN chmod +x /home/user/run.sh

# Run server.
USER user

CMD /home/user/run.sh

EXPOSE 8080
