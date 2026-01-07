# Bootstrap de OIDC para GitHub Actions

Este módulo opcional crea:
- Proveedor OIDC de GitHub
- Rol IAM que el workflow de GitHub Actions puede asumir

## Gestión de Estado Remoto

El estado de OpenTofu se almacena en **S3 con locking en DynamoDB** para garantizar colaboración segura y prevenir conflictos. Esta configuración se eligió por las siguientes razones:

### Backend S3 + DynamoDB

**Componentes configurados:**
- **Bucket S3:** `lambda-automation-terraform-state-1767808613`
- **Tabla DynamoDB:** `terraform-locks`
- **Archivo de configuración:** `backend.tf`

**Ventajas de este enfoque:**

1. **Estado centralizado:** Múltiples desarrolladores pueden trabajar con el mismo estado compartido en S3, evitando divergencias entre estados locales.

2. **Prevención de conflictos:** DynamoDB proporciona mecanismos de locking que impiden que dos usuarios apliquen cambios simultáneamente, protegiendo contra la corrupción del estado.

3. **Versionamiento:** S3 permite habilitar versionamiento del archivo de estado, permitiendo recuperación ante errores.

4. **Costo mínimo:** Para archivos de estado pequeños (típicamente KB), el costo es inferior a $0.05 USD/mes. DynamoDB opera dentro del free tier de AWS.

### Importación de Recursos Existentes

Cuando los recursos de infraestructura ya existen en AWS pero no están en el estado de OpenTofu, se debe realizar una **importación** para evitar errores de tipo `EntityAlreadyExists`.

**Proceso de importación:**

```bash
# Ejemplo: importar rol IAM existente
tofu import aws_iam_role.lambda_exec hello-lambda-exec

# Ejemplo: importar función Lambda existente
tofu import aws_lambda_function.this hello-lambda
```

**Por qué es necesario:**

- OpenTofu mantiene un archivo de estado (`.tfstate`) que mapea los recursos declarados en código con los recursos reales en AWS.
- Si un recurso existe en AWS pero no en el estado, OpenTofu intentará crearlo nuevamente, generando un error.
- La importación sincroniza el estado existente de AWS con el estado local/remoto de OpenTofu sin modificar ni recrear recursos.

**Alternativas a la importación:**

1. **Destruir y recrear:** Eliminar el recurso en AWS y permitir que OpenTofu lo cree desde cero (no recomendado en producción).
2. **Backend desde el inicio:** Si se configura el backend remoto antes de crear recursos, todo el equipo comparte el mismo estado desde el principio.

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
tofu init  # Se conectará automáticamente al backend S3
tofu apply -auto-approve
```

   **Nota:** Si los recursos ya existen en AWS, será necesario importarlos antes de aplicar:
   ```bash
   tofu import aws_iam_openid_connect_provider.github arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com
   tofu import aws_iam_role.gha_oidc NOMBRE_DEL_ROL
   ```

4. Copia el valor de salida `role_to_assume` a los Secrets del repo:
   - `AWS_ROLE_TO_ASSUME` = valor de `role_to_assume`
   - `AWS_REGION` = el que usaste (ej. `us-east-1`)

Tras esto, el push a main aplicará los cambios de `infra/` automáticamente.

## Migración de Estado Local a S3

Si se trabajó previamente con estado local (`.tfstate` en disco), se puede migrar al backend S3 ejecutando:

```bash
cd bootstrap
tofu init -migrate-state
```

OpenTofu detectará el estado local existente y ofrecerá copiarlo al bucket S3 configurado. Una vez migrado, el archivo `.tfstate` local puede eliminarse (ya está excluido en `.gitignore`).

## Costos y Recursos

### Recursos sin costo:
- Rol IAM y proveedor OIDC: **$0** (IAM es gratuito)

### Recursos con costo mínimo:
- **S3 (estado):** ~$0.01-0.02 USD/mes (almacenamiento de KB)
- **DynamoDB (locks):** $0 (free tier cubre el uso de locking)

**Costo total estimado:** < $0.05 USD/mes

El rol OIDC debe mantenerse entre despliegues. Solo debe eliminarse cuando el proyecto finalice completamente.
