FROM python
USER 0
RUN pip install --upgrade pip

COPY . ./

RUN pip install -U setuptools
RUN pip install -r requirements.txt

RUN chmod u+x start.sh

ENTRYPOINT ["./start.sh"]
