FROM tiangolo/uwsgi-nginx-flask:python3.7
RUN python -m pip install healpy pygcn ligo.skymap astropy pyephem pandas
RUN python -m pip install mysql-connector
RUN python -m pip install sqlalchemy pymysql
COPY ./app /app
