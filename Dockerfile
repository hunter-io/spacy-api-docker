FROM phusion/passenger-customizable:latest

RUN apt-get install -y --no-install-recommends python3

# RUN /pd_build/python.sh

CMD ["/sbin/my_init"]

RUN mkdir /app
WORKDIR /app
ENV HOME /app

# Install the required packages
RUN apt-get update
RUN apt-get install -y \
    build-essential \
    libssl-dev \
    supervisor \
    curl \
    vim-tiny \
    python3-pip

RUN pip3 install --upgrade pip
RUN pip3 install falcon spacy falcon requests pathlib

# Nginx
RUN rm -f /etc/service/nginx/down
RUN rm /etc/nginx/sites-enabled/default
RUN rm /etc/nginx/sites-available/default
ADD webapp.conf /etc/nginx/sites-enabled/webapp.conf

# Python application
ADD app/ /app/
ADD passenger_wsgi.py /app/passenger_wsgi.py
RUN chown -R app:app /app


# # Copy and set up the app
# COPY displacy_service/ /app/displacy_service
# COPY start.sh /app/start.sh
# COPY setup.py /app/setup.py
# COPY Makefile /app/Makefile
# RUN cd /app && make clean

# # ENV languages "en_core_web_lg"
# # RUN cd /app && env/bin/download_models

# ENV PORT 8000
# EXPOSE 8000
# CMD ["bash", "/app/start.sh"]
# passenger start --python /usr/bin/python3
