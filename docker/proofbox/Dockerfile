# proofbox: native CaDiCaL 3.0.1 + drat-trim (DRAT certification), built from the bundled source archives (no git access needed)
FROM debian:trixie-slim
RUN apt-get update && apt-get install -y --no-install-recommends g++ make && rm -rf /var/lib/apt/lists/*
COPY cadical.tar.gz drat-trim.tar.gz /opt/
RUN cd /opt && tar xzf cadical.tar.gz && cd cadical-master && ./configure && make -j4 && cp build/cadical /usr/local/bin/
RUN cd /opt && tar xzf drat-trim.tar.gz && cd drat-trim-master && gcc -O2 -D_GNU_SOURCE -o drat-trim drat-trim.c && cp drat-trim /usr/local/bin/
WORKDIR /w
