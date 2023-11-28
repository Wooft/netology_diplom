FROM python:3.11-alpine

WORKDIR /usr/src/product_automation
COPY ./requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .
RUN sed -i 's/\r$//g' /usr/src/product_automation/entrypoint.sh
RUN chmod +x /usr/src/product_automation/entrypoint.sh