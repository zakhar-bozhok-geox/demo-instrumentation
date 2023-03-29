FROM python:3.10 AS py_demo

COPY . /app
RUN pip install -r /app/deps.txt
WORKDIR /app
CMD [ "python3",  "main.py"]