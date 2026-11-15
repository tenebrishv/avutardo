# Tracker de issues: GitHub

Las issues y las specs de este repo viven en las GitHub Issues de
`tenebrishv/avutardo`. Todas las operaciones van con el CLI `gh`.

## Reglas propias del repo

- Títulos y cuerpos en **español**. Números con punto decimal y unidades SI.
- Los requisitos se citan por su código del Anexo A v2 (`G3`, `X1`, `F1`).
- El repo va a ser **público**: sin mails, claves ni datos personales en las
  issues ni en los comentarios.
- Una issue puede **pedir** una decisión del equipo (campos de telemetría,
  comandos, herramientas del firmware), nunca tomarla.
- Antes de crear issues, etiquetas o milestones en lote, confirmar con el
  usuario: todo lo que se crea en GitHub queda publicado.

## Convenciones

- **Crear una issue**: `gh issue create --title "..." --body "..."`. Para
  cuerpos de varias líneas, usar un heredoc.
- **Leer una issue**: `gh issue view <número> --json number,title,body,labels,comments`.
- **Listar issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'`
  con los filtros `--label` y `--state` que hagan falta.
- **Hacer una issue sub-issue de otra**: `gh issue create --parent <padre> ...`,
  o después `gh issue edit <padre> --add-sub-issue <hija>` (`gh` 2.94 o más
  nuevo). Con un `gh` más viejo:
  `gh api --method POST repos/<dueño>/<repo>/issues/<padre>/sub_issues -F sub_issue_id=<database-id-de-la-hija>`
  (el database id, como en **Bloqueos**). Sin sub-issues, poner
  `Part of #<padre>` al principio del cuerpo de la hija.
- **Bloqueos**: las **dependencias nativas** de GitHub, que se ven en la
  interfaz. Para sumar una arista: `gh issue create --blocked-by <n>,<n> ...` o
  `gh issue edit <hija> --add-blocked-by <bloqueante>` (`gh` 2.94 o más nuevo).
  Con un `gh` más viejo:
  `gh api --method POST repos/<dueño>/<repo>/issues/<hija>/dependencies/blocked_by -F issue_id=<database-id-del-bloqueante>`,
  donde el database id es el numérico
  (`gh api repos/<dueño>/<repo>/issues/<n> --jq .id`; _no_ el `#número` ni el
  `node_id`). Si las dependencias no están disponibles, usar una línea
  `Blocked by: #<n>, #<n>` al principio del cuerpo de la hija. Un ticket se
  desbloquea cuando todos sus bloqueantes están cerrados.
- **Contar los bloqueantes abiertos**:
  `gh api repos/<dueño>/<repo>/issues/<n> --jq .issue_dependencies_summary.blocked_by`
  (sólo los abiertos; 0 quiere decir que se puede empezar).
  `gh issue view <n> --json blockedBy` también trae los cerrados, así que hay
  que filtrarlo: `--jq '[.blockedBy.nodes[] | select(.state == "OPEN")] | length'`.
- **Comentar una issue**: `gh issue comment <número> --body "..."`
- **Poner / sacar etiquetas**: `gh issue edit <número> --add-label "..."` / `--remove-label "..."`
- **Cerrar**: primero la explicación con `gh issue comment <número> --body "..."`
  y después `gh issue close <número>`. Sobre una issue ya cerrada,
  `gh issue close --comment` descarta el comentario y sale igual con código 0.

El repo se infiere de `git remote -v`: `gh` lo hace solo cuando corre adentro
del clon.

Las issues se abren sólo en este repo. Nunca en `mattpocock/skills` (el repo
de donde vienen las skills). Antes del primer `gh issue create` de la sesión,
confirmar el destino con `gh repo view --json nameWithOwner`.

## Pull requests como entrada de triage

**PRs as a request surface: no.** _(Poner `yes` si este repo toma los PR
externos como pedidos de funcionalidad; `/triage` lee este valor.)_

Con `yes`, los PR pasan por las mismas etiquetas y estados que las issues, con
los equivalentes de `gh pr`:

- **Leer un PR**: `gh pr view <número>`, después `gh pr view <número> --comments`
  (fuera de una terminal, `--comments` imprime sólo los comentarios, sin el
  cuerpo) y `gh pr diff <número>` para el diff.
- **Listar PR externos para triage**:
  `gh api --paginate 'repos/{owner}/{repo}/pulls?state=open' --jq '.[] | select(.author_association | IN("OWNER","MEMBER","COLLABORATOR") | not) | {number, title, author: .user.login, author_association, labels: [.labels[].name]}'`.
- **Comentar / etiquetar / cerrar**: `gh pr comment`, `gh pr edit --add-label`/`--remove-label`, `gh pr close`.

GitHub comparte la numeración entre issues y PR, así que un `#42` suelto puede
ser cualquiera de los dos: resolverlo con `gh pr view 42` y, si falla,
`gh issue view 42`.

## Cuando una skill dice "publicar en el tracker"

Crear una issue de GitHub.

## Cuando una skill dice "traer el ticket"

Leerlo como en **Leer una issue**.

## Operaciones de wayfinding

Las usa `/wayfinder`. El **mapa** es una sola issue y los tickets son issues
**hijas**.

- **Mapa**: una issue con la etiqueta `wayfinder:map`, cuyo cuerpo tiene las
  secciones Notes / Decisions-so-far / Fog. `gh issue create --label wayfinder:map`.
- **Ticket hijo**: una issue vinculada al mapa como sub-issue de GitHub (ver
  **Hacer una issue sub-issue de otra**). Si las sub-issues no están
  habilitadas, sumar la hija a una lista de tareas en el cuerpo del mapa y
  poner `Part of #<mapa>` al principio del cuerpo de la hija. Etiquetas:
  `wayfinder:<tipo>` (`research`/`prototype`/`grilling`/`task`). Al tomarlo, el
  ticket se asigna a quien lo lleva.
- **Bloqueos**: ver **Bloqueos** en Convenciones.
- **Consulta de frontera**: listar las hijas abiertas del mapa
  (`gh issue list --state open`, acotado a las sub-issues o a la lista de
  tareas del mapa), descartar las que tengan un bloqueante abierto (ver
  **Contar los bloqueantes abiertos**, o una issue abierta en la línea
  `Blocked by`) o una persona asignada; gana la primera en el orden del mapa.
- **Tomar**: `gh issue edit <n> --add-assignee @me`; es la primera escritura de
  la sesión.
- **Resolver**: `gh issue comment <n> --body "<respuesta>"`, después
  `gh issue close <n>`, y después sumar un puntero de contexto (resumen +
  enlace) a la sección Decisions-so-far del mapa.
