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

docker build -t jvicient/reg_water_flask:latest -t jvicient/reg_water_flask:$versio -f reg_water_flask/Dockerfile .

# run it
#docker run jvicient/reg_water_flask

echo "To push to dockerhub:"
echo "docker push jvicient/reg_water_flask:latest"
echo "docker push jvicient/reg_water_flask:"$versio
