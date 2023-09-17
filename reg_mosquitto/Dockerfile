FROM eclipse-mosquitto:latest

ENV CONFIG_FILE /mosquitto/config/mosquitto.conf
ENV TZ Europe/Andorra

RUN rm $CONFIG_FILE
RUN echo 'allow_anonymous true' >> $CONFIG_FILE
RUN echo 'listener 1883' >> $CONFIG_FILE

#CMD cat $CONFIG_FILE