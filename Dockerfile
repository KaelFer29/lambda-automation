# Imagen base con Playwright y navegadores
FROM mcr.microsoft.com/playwright/python:v1.57.0-jammy

# Directorio de trabajo donde Lambda buscará el handler
WORKDIR /var/task

# Copiar el código del handler (módulo de Lambda)
COPY src/dte-fetcher/ /var/task/

# Instalar el runtime interface client de AWS Lambda
RUN pip install --no-cache-dir awslambdaric

# Comando del handler (module.function)
CMD ["handler.lambda_handler"]

# Entry point para el runtime de Lambda en contenedores
ENTRYPOINT ["python", "-m", "awslambdaric"]
