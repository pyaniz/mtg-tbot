FROM python:3.8
 
WORKDIR /Bot
COPY . /Bot
 
RUN pip install -r requirements.txt
 
ENTRYPOINT ["python"]
CMD ["./Bot/main.py"]