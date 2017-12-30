FROM python:2
MAINTAINER Phyks <phyks@phyks.me>

# Setup layout.
RUN useradd -d /home/user -m -s /bin/bash -U user

# Install OS dependencies.
RUN apt-get update && \
    apt-get install -y git libffi-dev \
    libxml2-dev libxslt-dev libyaml-dev libtiff-dev libjpeg-dev zlib1g-dev \
    libfreetype6-dev libwebp-dev build-essential gcc g++ wget;

# Install latest pip and python dependencies.
RUN pip install -U setuptools && \
    pip install html2text simplejson BeautifulSoup

# Install node.js.
RUN curl -sL https://deb.nodesource.com/setup_8.x | bash - \
    && apt-get install -y nodejs

# Install weboob's code itself.
RUN git clone https://git.weboob.org/weboob/devel /home/user/weboob \
    && cd /home/user/weboob \
    && pip install .

RUN mkdir -p /flatisfy/data
VOLUME /flatisfy

# Install Flatisfy.
RUN cd /home/user \
    && git clone https://git.phyks.me/Phyks/flatisfy/ ./app \
    && cd ./app \
    && pip install -r requirements.txt \
    && pip install functools32 \
    && npm install \
    && npm run build:prod

RUN chown user:user -R /home/user
RUN mkdir -p /home/user/.local/share/flatisfy

COPY ./run.sh /home/user/run.sh
RUN chmod +x /home/user/run.sh
COPY ./update_weboob.sh /home/user/update_weboob.sh
RUN chmod +x /home/user/update_weboob.sh

# Run server.
EXPOSE 8080
CMD /home/user/run.sh
