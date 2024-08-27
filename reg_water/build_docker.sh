#!/bin/bash

# Comprovar que hi ha exactament un paràmetre
if [ "$#" -ne 1 ]; then
    echo "Es requereix la revisió de codi com a paràmetre."
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

docker build -t jvicient/reg_water:latest -t jvicient/reg_water:$versio -f reg_water/Dockerfile .

echo run it executing:
echo docker run -p 5002:5002 jvicient/reg_water

# push
echo publich executing:
echo "docker push jvicient/reg_water:"$versio
echo "docker push jvicient/reg_water:latest"
