FROM python:alpine
LABEL org.opencontainers.image.source https://github.com/keitharm/homecontrol
RUN pip install smartrent.py flask asgiref
WORKDIR /app
COPY main.py .
ENTRYPOINT ["python", "main.py"]