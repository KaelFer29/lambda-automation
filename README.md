# Lambda Automation con OpenTofu + GitHub Actions

Este repo despliega una Lambda en AWS usando OpenTofu (Terraform compatible) y CI/CD desde GitHub Actions.

El estado de Terraform se guarda **localmente** (en el runner de GitHub Actions), sin necesidad de S3 ni DynamoDB. Esto es suficiente para proyectos individuales o pequeños equipos.

## Estructura
- infra/: Infraestructura con OpenTofu
- src/hello/: Código de la Lambda (Python 3.12)
- .github/workflows/deploy.yml: Pipeline CI/CD

## Flujo CI/CD
- Pull Request a main: `tofu init` + `tofu plan` (sin aplicar)
- Push a main: `tofu init` + `tofu plan` + `tofu apply` (aplica cambios)

## Requisitos
1) AWS OIDC para GitHub Actions (rol que el workflow asume)
2) Secrets del repo configurados:
   - `AWS_ROLE_TO_ASSUME`: ARN del rol OIDC para GitHub
   - `AWS_REGION`: región de AWS (ej. `us-east-1`)

Puedes usar el módulo `bootstrap/` para crear automáticamente el rol OIDC.

## Despliegue local (con credenciales AWS)
```bash
cd infra
# Edita variables en variables.tf si deseas
tofu init
tofu plan
tofu apply
```

## Despliegue por CI/CD (sin credenciales de larga vida)
1. Crea el rol OIDC con `bootstrap/` o manualmente (ver [bootstrap/README.md](bootstrap/README.md)).
2. Configura los 2 secrets (`AWS_ROLE_TO_ASSUME`, `AWS_REGION`).
3. Haz push a `main`. El workflow asume el rol OIDC y despliega la Lambda.

## Cambiar el runtime o el código
Edita `src/hello/handler.py` o modifica `infra/main.tf` para cambiar `runtime`, `handler`, nombre, etc.
