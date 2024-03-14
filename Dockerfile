FROM python:3.11

COPY . /app
RUN pip install -r /app/requirements.txt
WORKDIR /data

VOLUME /data
CMD ["python", "bot.py"]