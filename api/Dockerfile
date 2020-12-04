FROM python:3.7

#update
RUN apt-get update

#install requirements
COPY requirements.txt /tmp/requirements.txt
WORKDIR /tmp
RUN pip3 install -r requirements.txt
RUN python -c "import nltk; nltk.download('stopwords')"
#RUN python -m nltk.downloader punkt

#copy app
COPY . /api
WORKDIR /

#CMD ["gunicorn", "-w", "3", "-b", ":5000", "-t", "360", "--reload", "api.wsgi:app"]

CMD gunicorn -w 10 --threads 4 --worker-class gthread --bind :5000 -t 360 --reload api.wsgi:app
