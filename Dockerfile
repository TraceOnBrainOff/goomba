FROM python:3.11-slim

WORKDIR /app

#Installing required packages
COPY ./packages.txt ./
RUN xargs sudo apt-get install <packages.txt

#Creating virtual python env
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

#Install packages to venv
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./src

CMD ["python3", "src/main.py"]