#!/bin/bash

# Comprovar que hi ha exactament un paràmetre
if [ "$#" -ne 1 ]; then
    echo "Es requereix exactament un paràmetre."
    exit 1
fi

# Obtenir el paràmetre
versio="$1"

# Comprovar que el paràmetre només conté números, lletres o '.'
if [[ "$versio" =~ ^[a-zA-Z0-9.]+$ ]]; then
    echo "Creant versió: "$versio
else
    echo "El paràmetre no és vàlid. Només es permeten números, lletres o '.'."
    exit 1
fi

cd "$(dirname "$0")"
cd ..

ls -la

docker build -t jvicient/reg_telegram:latest -t jvicient/reg_telegram:$versio -f reg_telegram/Dockerfile .

# run it
#docker run --env-file reg_telegram/.env jvicient/reg_telegram

echo "To push to dockerhub:"
echo "docker push jvicient/reg_telegram:latest"
echo "docker push jvicient/reg_telegram:"$versio