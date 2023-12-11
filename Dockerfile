FROM raviqqe/muffet

RUN apk add --no-cache python3 py3-requests py3-requests-futures

COPY ./website-link-checker.py /

ENTRYPOINT ["/usr/bin/python", "/website-link-checker.py"]
