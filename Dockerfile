FROM alpine:latest

# Install Go
RUN apk add --no-cache git make musl-dev go

# Configure Go
ENV GOROOT /usr/lib/go
ENV GOPATH /go
ENV PATH /go/bin:$PATH

RUN mkdir -p ${GOPATH}/src ${GOPATH}/bin
RUN export PATH=$PATH:$GOPATH/bin

# Install Muffet
RUN go install github.com/raviqqe/muffet/v2@latest

# Install python/pip
ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools

# Install the link checker python program
RUN mkdir -p ${HOME}/programs
COPY ./website-link-checker.py ${HOME}/programs/website-link-checker.py

# Set the working directory
WORKDIR ${HOME}/programs

# Give execution permission to the link checker
RUN chmod +x ./website-link-checker.py

# Run the link checker
RUN python ./website-link-checker.py https://www2.mycelium.threefold.io/ -w all -e 404