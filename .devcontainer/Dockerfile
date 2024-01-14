FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN apt-get -y update
RUN apt-get -y install git
RUN pip install -r requirements.txt
EXPOSE 8080
CMD streamlit run main.py