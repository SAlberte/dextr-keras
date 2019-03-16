FROM python:3.6

WORKDIR /temp/
ADD requirements.txt /temp/
RUN pip install -r requirements.txt && \
    pip install pycocotools

WORKDIR /workspace/

EXPOSE 8888
CMD jupyter notebook --port=8888 --ip=0.0.0.0 --no-browser --allow-root