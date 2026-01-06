# Lambda Automation con OpenTofu + GitHub Actions

Sistema de despliegue continuo (CI/CD) para funciones Lambda en AWS. Al realizar un push a la rama `main`, el código se valida y se despliega automáticamente en AWS sin intervención manual.

## Descripción general

Se implementa un flujo de trabajo automatizado donde el código de la Lambda y su infraestructura se versionan en Git. Los cambios se validan mediante `tofu plan` en cada Pull Request y se despliegan automáticamente al mergear a `main`. Se utiliza autenticación OIDC para obtener credenciales temporales, evitando guardar secretos permanentes en GitHub.

## Estructura del proyecto

```
lambda-automation/
├── infra/                   # Infraestructura con OpenTofu
│   ├── main.tf              # Lambda, roles IAM, empaquetado
│   ├── variables.tf         # Variables (región, nombre función)
│   └── outputs.tf           # Outputs (ARN, nombre Lambda)
├── src/hello/
│   └── handler.py           # Código Python de la Lambda
├── bootstrap/               # Configuración inicial (OIDC)
│   ├── main.tf
│   ├── variables.tf
│   └── README.md
├── .github/workflows/
│   └── deploy.yml           # Pipeline CI/CD
├── .gitignore
└── README.md
```

## Componentes principales

### infra/main.tf
Define la infraestructura mediante OpenTofu. Incluye:
- `archive_file`: Empaqueta el código en un `.zip`.
- `aws_iam_role`: Rol de ejecución para la Lambda con permisos básicos.
- `aws_lambda_function`: Función Lambda con Python 3.12, timeout de 10 segundos.

El estado de Terraform se guarda localmente en el runner de GitHub Actions, configuración apropiada para un solo desarrollador sin costos adicionales. Para equipos más grandes, se recomienda migrar a un backend remoto (S3 + DynamoDB).

### src/hello/handler.py
Código Python ejecutable en la Lambda. Se modifica según los requerimientos funcionales.

### .github/workflows/deploy.yml
Pipeline automatizado que:
- En Pull Request: Valida cambios con `tofu plan` sin aplicarlos.
- En push a `main`: Ejecuta `tofu init`, `tofu plan` y `tofu apply`.

Se autentica mediante OIDC para obtener credenciales temporales de AWS.

### bootstrap/
Módulo de inicialización que crea:
- Proveedor OIDC: Autoriza a AWS para confiar en tokens de GitHub Actions.
- Rol IAM: Permite a GitHub Actions interactuar con AWS.

Se ejecuta una sola vez; el rol creado se reutiliza en cada despliegue.

## Conceptos clave

### OIDC (OpenID Connect)
Estándar de autenticación que permite obtener credenciales temporales de AWS sin guardar claves permanentes en GitHub. Las credenciales tienen tiempo de expiración limitado (minutos) y se renueva automáticamente en cada ejecución del workflow.

### ARN (Amazon Resource Name)
Identificador único de recursos en AWS. Ejemplo:
```
arn:aws:iam::123456789012:role/lambda-automation-gha-oidc
```
Se utiliza en el secret `AWS_ROLE_TO_ASSUME` para indicar qué rol debe asumir GitHub Actions.

### Estado de Terraform (terraform.tfstate)
Archivo JSON que registra la infraestructura actual en AWS. Se puede guardar en:
- **Local** (configuración actual): Guardado en el runner de GitHub. Apropiado para un solo desarrollador.
- **Remoto (S3)**: Guardado en AWS S3. Necesario cuando múltiples máquinas necesitan acceder al mismo estado.
- **Con locks (DynamoDB)**: Previene conflictos si dos personas ejecutan cambios simultáneamente. Recomendado para equipos.

## Configuración inicial

### Paso 1: Instalar AWS CLI
```bash
sudo snap install aws-cli --classic
aws --version
```

### Paso 2: Configurar credenciales AWS
```bash
aws configure
```
Se solicita:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (recomendado: `us-east-1`)
- Default output format (opcional)

Para obtener las credenciales:
1. Acceder a AWS Console → IAM → Users.
2. Crear un usuario con permisos `AdministratorAccess`.
3. Security credentials → Create access key → Download CSV.
4. Pegar los valores en `aws configure`.

### Paso 3: Ejecutar bootstrap
```bash
cd bootstrap
tofu init
tofu apply \
  -var "github_org=KaelFer29" \
  -var "github_repo=lambda-automation"
```

Retorna el ARN del rol:
```
role_to_assume = "arn:aws:iam::123456789012:role/lambda-automation-gha-oidc"
```

### Paso 4: Configurar secrets en GitHub
1. Acceder al repositorio en GitHub.
2. Settings → Secrets and variables → Actions.
3. Crear dos secrets:
   - `AWS_ROLE_TO_ASSUME` = ARN obtenido en Paso 3.
   - `AWS_REGION` = `us-east-1`.

### Paso 5: Realizar el primer push
```bash
git config --global user.name "Nombre"
git config --global user.email "email@ejemplo.com"
git add .
git commit -m "chore: bootstrap OIDC role"
git push origin main
```

GitHub requiere autenticación con PAT o SSH, no con contraseña.

### Paso 6: Verificar despliegue
1. Acceder a GitHub → Actions → "CI/CD Lambda".
2. Verificar que la última ejecución sea exitosa.
3. Comprobar Lambda en AWS:
```bash
aws lambda list-functions --region us-east-1
aws lambda get-function --function-name hello-lambda --region us-east-1
```

## Flujo de trabajo

### Modificar código de la Lambda
1. Editar `src/hello/handler.py`.
2. Realizar commit y push a `main`.
3. El workflow se ejecuta automáticamente y despliega la Lambda.

### Modificar infraestructura
1. Editar `infra/main.tf` (nombre, timeout, memoria, etc.).
2. Realizar commit y push a `main`.
3. El workflow ejecuta `tofu plan` y `tofu apply` para aplicar los cambios.

### Revisar cambios antes de desplegar
1. Crear una rama y realizar cambios.
2. Abrir un Pull Request a `main`.
3. El workflow ejecuta `tofu plan` mostrando los cambios sin aplicarlos.
4. Después de revisar, mergear a `main` para desplegar.

## Escalabilidad para equipos

### Problema con múltiples desarrolladores
Si varios miembros del equipo realizan cambios simultáneamente sin un backend remoto:
- Cada runner tiene su propia copia del estado.
- Dos `apply` simultáneos pueden causar inconsistencias en la infraestructura.

### Solución: S3 + DynamoDB

**S3 (backend remoto):**
- Centraliza el archivo `terraform.tfstate` en la nube.
- Todos los runners acceden al mismo estado.
- Se sincroniza automáticamente antes y después de cada operación.

**DynamoDB (locks):**
- Mientras un miembro aplica cambios, otros quedan bloqueados.
- Previene race conditions y conflictos de sincronización.
- Costo mínimo en capa gratuita con modo PAY_PER_REQUEST.

**Implementación:**
1. Descomentar o crear S3 y DynamoDB en `bootstrap/main.tf`.
2. Ejecutar `tofu apply` en bootstrap.
3. Configurar el workflow para usar backend remoto con `-backend-config`.

**Cuándo implementar:**
- Equipo con más de un desarrollador.
- Cambios frecuentes y simultáneos.
- Proyecto en producción.

**Costos aproximados:**
- S3: ~$0.023 por GB/mes (típicamente menos de 1 GB).
- DynamoDB: Gratuito en capa libre con PAY_PER_REQUEST.

## Despliegue local (opcional)

Para probar cambios sin usar CI/CD:
```bash
cd infra
tofu init
tofu plan    # muestra cambios
tofu apply   # aplica localmente
```

## Personalización

### Cambiar nombre de la función
Editar `infra/variables.tf`:
```hcl
variable "function_name" {
  default = "nombre-personalizado"
}
```

### Cambiar runtime
Editar `infra/main.tf`:
```hcl
resource "aws_lambda_function" "this" {
  runtime = "nodejs20.x"  # cambiar de python3.12
  handler = "index.handler"
  ...
}
```

### Ajustar timeout y memoria
Editar `infra/main.tf`:
```hcl
resource "aws_lambda_function" "this" {
  timeout     = 60        # segundos
  memory_size = 512       # MB
  ...
}
```

## Consideraciones de seguridad

1. **Autenticación:** Utilizar OIDC en lugar de claves de acceso permanentes.
2. **Permisos:** Reducir permisos del rol a mínimo privilegio requerido.
3. **Revisión de cambios:** Revisar siempre el `tofu plan` en PRs antes de mergear a `main`.
4. **Logs:** Evitar registrar información sensible en logs públicos.

## Troubleshooting

**Workflow falla con error OIDC:**
- Verificar que `AWS_ROLE_TO_ASSUME` sea correcto.
- Verificar que `AWS_REGION` sea válido.

**Lambda no aparece en AWS:**
- Verificar que el workflow sea exitoso en GitHub Actions.
- Verificar región: `aws lambda list-functions --region us-east-1`.

**Estado corrupto:**
- Eliminar: `rm -r infra/.terraform infra/.terraform.lock.hcl`.
- Reinicializar: `tofu init`.