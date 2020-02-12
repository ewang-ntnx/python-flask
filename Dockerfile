from alpine:latest

RUN apk update && apk add bash
RUN apk add openssh
RUN apk add sshpass
RUN apk add --no-cache python3-dev \
    && pip3 install --upgrade pip


RUN ssh-keygen -q -t rsa -N '' -f ~/.ssh/id_rsa
RUN sshpass -f password.txt ssh-copy-id -o StrictHostKeyChecking=no nutanix@172.17.0.1
WORKDIR /app

COPY . /app

RUN pip3 --no-cache-dir install -r requirements.txt

EXPOSE 5000

ENTRYPOINT ["python3"]
CMD ["app.py"]
