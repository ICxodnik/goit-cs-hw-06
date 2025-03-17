FROM python:3.13

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "app.py", "runserver", "0.0.0.0:8000"]