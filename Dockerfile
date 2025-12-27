FROM python:3.12-slim
RUN pip install --upgrade pip
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENV FLASK_APP=/app/app.py
EXPOSE 80
ENTRYPOINT python app.py