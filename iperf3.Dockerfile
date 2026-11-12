FROM alpine:3.21
RUN apk add --no-cache iperf3
USER 65534:65534
EXPOSE 5201/tcp 5201/udp
ENTRYPOINT ["iperf3"]
CMD ["-s","-p","5201"]
