FROM python:3.10

RUN mkdir /translation_app

WORKDIR  /translation_app

COPY ./translatiion_service/requirements.txt /translation_app

ENV PYTHONUNBUFFERED 1

RUN apt update && apt install -y gettext
RUN pip install --upgrade pip

RUN pip install -r requirements.txt

COPY ./translatiion_service .

COPY ./grpc_translations /translation_app/grpc_translations

RUN pip install -e ./grpc_translations/
