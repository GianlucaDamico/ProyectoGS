Equipo de 4 trabajando siempre en `master`

---

## Filosofía de trabajo

Trabajamos directamente sobre `master`.
Para que el repositorio no se vuelva inestable seguimos cuatro principios:

1. Sincronizar antes y después de trabajar.
2. Hacer commits pequeños y frecuentes.
3. No reescribir historial.
4. Resolver conflictos con calma y método.

---

## Instalación y conexión

## 1. Instalar Git
- Instalar Git en el sistema operativo.
- Reiniciar VS Code después de la instalación.

## 2. Iniciar sesión en GitHub desde VS Code
1. Abrir VS Code.
2. Ir al icono de cuenta (esquina inferior izquierda).
3. Seleccionar **Sign in with GitHub**.
4. Autorizar desde el navegador.

Recomendado usar HTTPS para simplificar la autenticación.

---

# Clonar repositorio desde la interfaz

1. `Ctrl + Shift + P`
2. Escribir `Git: Clone`
3. Pegar la URL del repositorio.
4. Elegir carpeta destino.
5. Abrir proyecto.

---

# Flujo de trabajo recomendado en master

## Paso 1 – Sincronizar antes de empezar

En Source Control:
- Pulsar **Sync Changes**
  o `...` → Pull (Rebase)

Esto asegura que estás trabajando sobre la última versión de `master`.

---

## Paso 2 – Trabajar en bloques pequeños

Recomendaciones:
- No trabajar durante horas sin hacer commit.
- No acumular muchos archivos en un solo commit.
- Hacer un commit por cada cambio lógico.

---

## Paso 3 – Crear commit desde la UI

1. Stage con `+` los archivos modificados.
2. Escribir mensaje claro y específico.
3. Pulsar **Commit**.
4. Pulsar **Sync Changes**.

---

# Gestión de conflictos

Si dos personas editan el mismo archivo:

VS Code abrirá el Merge Editor con tres paneles:
- Cambios locales
- Cambios remotos
- Resultado final

Opciones disponibles:
- Accept Current
- Accept Incoming
- Accept Both

Después:
1. Guardar archivo.
2. Hacer Stage.
3. Pulsar Sync.

---

# Normas internas del equipo

- Avisar si se va a modificar un archivo crítico.
- No usar Force Push.
- Si se rompe algo, solucionarlo con un nuevo commit.
- Mantener comunicación mínima para evitar conflictos repetidos.

---

# Autenticación

Si GitHub solicita autenticación:
- Autorizar desde navegador.
- VS Code guarda el token automáticamente.

Si falla:
- Cerrar sesión en VS Code.
- Iniciar sesión nuevamente.

---

# Problemas comunes

## Push rechazado
Solución:
- `...` → Pull (Rebase)
- Resolver conflictos si aparecen
- Sync Changes

## Archivo que no debía subirse
1. Añadir nombre al `.gitignore`.
2. Stage del `.gitignore`.
3. Commit.
4. Sync.

## Commit que rompió el proyecto
En Timeline:
- Click derecho → Revert Commit.
- Sync.

---

# Uso opcional de ramas (sin jerarquía)

Si el cambio es grande:
1. `Ctrl + Shift + P`
2. `Git: Create Branch`
3. Trabajar en esa rama.
4. Cambiar a master.
5. Merge desde la UI.

---

# Flujo real del día a día

El 90% del tiempo el ciclo será:

1. Sync
2. Editar
3. Stage
4. Commit
5. Sync
