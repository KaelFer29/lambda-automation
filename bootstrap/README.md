# Bootstrap de OIDC para GitHub Actions

Este módulo opcional crea:
- Proveedor OIDC de GitHub
- Rol IAM que el workflow de GitHub Actions puede asumir

El estado de Terraform se guarda **localmente** en tu máquina, sin necesidad de S3 ni DynamoDB.

## Uso
1. Asegúrate de tener credenciales AWS locales (perfil con permisos de admin).
2. Define variables mínimas:

```bash
export TF_VAR_github_org="<tu_org_o_usuario>"
export TF_VAR_github_repo="<tu_repo>"
# opcional
export TF_VAR_github_branch="main"
export TF_VAR_aws_region="us-east-1"
```

3. Inicializa y aplica:
```bash
cd bootstrap
tofu init
tofu apply -auto-approve
```

4. Copia el valor de salida `role_to_assume` a los Secrets del repo:
   - `AWS_ROLE_TO_ASSUME` = valor de `role_to_assume`
   - `AWS_REGION` = el que usaste (ej. `us-east-1`)

Tras esto, el push a main aplicará los cambios de `infra/` automáticamente.

## Capa gratuita
- El rol OIDC es un recurso de IAM **sin costo**.
- Mantén el rol entre despliegues; solo bórralo cuando termines el proyecto.
