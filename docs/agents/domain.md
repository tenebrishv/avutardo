# Documentos del dominio

Cómo tienen que leer las skills de ingeniería la documentación del dominio de
este repo al explorar el código. El repo es de **un solo contexto**.

## Antes de explorar, leer

- **`GLOSSARY.md`**, en la raíz del repo: el glosario.
- **`docs/adr/`**: los ADR que toquen la zona en la que se va a trabajar.
- **`docs/gcs-decisiones.md`**: las decisiones de la estación terrena y su
  porqué, anteriores a los ADR. Leerlo antes de proponer un cambio de diseño
  en `gcs/`.
- **`protocolo/telemetria.toml`**: la única fuente del formato de telemetría.

Si alguno no existe, **seguir sin decir nada**. No marcar que falta ni proponer
crearlo de antemano. La skill `/domain-modeling` (a la que se llega por
`/grill-with-docs` y `/improve-codebase-architecture`) los crea cuando hace
falta, a medida que se resuelven términos o decisiones.

## Estructura

```
/
├── GLOSSARY.md
├── docs/
│   ├── adr/
│   │   ├── 0001-....md
│   │   └── 0002-....md
│   └── gcs-decisiones.md
├── gcs/
├── protocolo/
└── firmware/
```

## Usar el vocabulario del glosario

Cuando lo que se escribe nombra un concepto del dominio (en el título de una
issue, una propuesta de refactor, una hipótesis, el nombre de un test), usar el
término tal como lo define `GLOSSARY.md`. No derivar a sinónimos que el glosario
descarta.

Si el concepto que hace falta todavía no está en el glosario, es una señal: o
se está inventando un lenguaje que el proyecto no usa (repensarlo), o hay un
hueco real (anotarlo para `/domain-modeling`).

## Señalar los choques con un ADR

Si lo que se escribe contradice un ADR existente (o `docs/gcs-decisiones.md`),
decirlo explícitamente en vez de pasarlo por encima en silencio:

> _Contradice el ADR-0007 (…), pero vale la pena reabrirlo porque…_
