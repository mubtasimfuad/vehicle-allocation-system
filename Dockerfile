FROM python:3.10

WORKDIR /app

COPY . /app

# dependencies
RUN pip install pipenv
RUN pipenv install --deploy --ignore-pipfile

EXPOSE 8000

CMD ["pipenv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
