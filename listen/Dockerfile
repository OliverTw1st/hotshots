FROM continuumio/miniconda3
RUN apt-get update
RUN apt-get install -y libc-dev
RUN apt-get install -y build-essential
RUN python -m pip install healpy pygcn ligo.skymap astropy pyephem pandas
RUN python -m pip install mysql-connector
RUN python -m pip install sqlalchemy pymysql
RUN python -m pip install slackclient
RUN conda install cartopy
RUN pip install wget
COPY listen.py .
COPY MS181101ab-1-Preliminary.xml .
CMD ["python", "listen.py"]
