# Rendering Pipelines, Platform Embedding Details, and Generating Diagrams from Source

Read this file before setting up CI/pre-commit rendering, before embedding a diagram in a
specific docs platform beyond what the main skill file's Platform Rendering Reality table
covers, or before deciding whether a diagram should be hand-maintained, generated, or deleted.

## Rendering pipeline options

- **Local jar** (`java -jar plantuml.jar -tsvg "**/*.puml"`): self-contained, the standard
  choice for CI. Needs a JVM, and needs Graphviz installed for the diagram types that require
  it (recent Windows builds bundle a minimal `dot` executable; Linux/macOS CI images still need
  Graphviz installed explicitly unless using `!pragma layout smetana`).
- **PlantUML server** (`docker run plantuml/plantuml-server`): a standing rendering service.
  This is what GitLab's native integration and many Confluence apps call out to. **Security
  note:** a self-hosted server can fetch network resources via `!include` from within a
  diagram — isolate it on the network and don't expose it to untrusted diagram input without
  restricting that.
- **Kroki**: a unified diagram-rendering API that fronts PlantUML alongside several other
  diagram languages; used by the common Antora and Docusaurus integrations. Note that Kroki and
  most remote-server setups generally do **not** run PlantUML's local-file `!include`
  preprocessor — a diagram that depends on including a local file won't render correctly
  through a remote/Kroki pipeline without pre-processing it first.

Pin a specific PlantUML version in CI for reproducibility — rendering output and available
pragmas/features can shift release to release.

## CI and pre-commit

- **CI job shape:** on push, render changed `.puml` files to SVG (or PNG) and either commit
  the rendered images back to the repo (necessary for GitHub, since it won't render PlantUML
  itself) or publish them as build artifacts (workable for GitLab, which can render natively).
  A common GitHub Actions pattern installs `graphviz` + the PlantUML jar, runs
  `plantuml -tsvg`, then auto-commits the rendered output.
- **Pre-commit:** run `plantuml -checkonly` (or `--check-syntax`, depending on version) to fail
  fast on a syntax error before it merges, without needing a full render. Community pre-commit
  hooks exist for this; wiring it in catches a broken diagram at commit time instead of at the
  next person's confused PR review.

## Per-platform embedding details beyond the main rendering-support table

- **GitHub:** besides committing a rendered image, the public PlantUML proxy can be used
  directly in an image URL — `https://www.plantuml.com/plantuml/proxy?cache=no&src=<raw URL to
  your .puml file>` — which re-renders on every view rather than requiring a commit step. There
  is also an official PlantUML browser extension that renders `.puml` files client-side when
  browsing GitHub, useful for local review but not something a reader without the extension
  benefits from.
- **GitLab:** the fenced `plantuml` Markdown block always rasterizes to PNG (not SVG) through
  GitLab's renderer. The `::include` directive can pull a `.puml` file from elsewhere in the
  repo into a rendered block, but it only resolves after the referenced file is committed —
  it will not show correctly in the merge-request diff preview before that.
- **Confluence:** because Cloud-hosted rendering apps typically send your diagram source to a
  vendor or public PlantUML render server, treat any diagram containing sensitive
  system/network topology as needing a self-hosted server (BYOS) rather than a Marketplace
  app's default hosted renderer.
- **MkDocs:** `plantuml-markdown` needs `pymdownx.superfences` configured to route fenced
  `plantuml` blocks to it; `mkdocs-build-plantuml-plugin` instead pre-generates image files at
  build time (no live rendering dependency for readers); `mkdocs-plantuml-local` renders
  without sending anything to a public server, for sensitive-content sites.

## Generating diagrams from source, instead of hand-maintaining them

Hand-maintained low-level diagrams are the ones that rot fastest. Where a diagram's content
already exists as structured source elsewhere, generate it instead of drawing it by hand:

- **From a database schema:** generate ER diagrams (see the main skill file's ER Diagrams
  section) from the live schema with a schema-introspection tool rather than hand-drawing
  entities and cardinalities that will drift the next time someone adds a column.
- **From an OpenAPI spec / FastAPI app:** tools exist that turn an OpenAPI document into
  PlantUML class/sequence views, keeping API-shape diagrams current with the actual contract
  instead of a stale hand-drawn approximation.
- **From Python domain models:** a class-diagram generator can walk domain module
  attributes/inheritance/composition and produce a current class diagram — a good fit for
  keeping a DDD domain layer's diagram honest without manual upkeep (see the
  `code-standards/python/references/ddd-clean-architecture.md` for the domain modeling patterns this would visualize).
- **From an architecture model (Structurizr DSL):** define the model (elements + relationships)
  once, then export multiple synchronized C4 `.puml` views from it via the CLI, instead of
  maintaining several C4 diagrams by hand and letting them drift apart from each other.

**The delete-or-generate test:** if keeping a diagram current requires manual effort, and the
same information is already available from code, an IDE, or another generated doc, delete the
diagram or wire up generation for it — don't maintain it by hand indefinitely. Applied to C4
specifically: Context and Container diagrams are almost always worth hand-maintaining (they
change slowly and carry real communication value); Component diagrams only for a container
complex enough to need one; Code-level diagrams only if generated, otherwise skip them
entirely.

**Review practice:** because `.puml` is text, review diagram changes in the same PR as the code
change they describe. A diagram diff with no corresponding code change (or vice versa) is worth
a second look — it's a common way diagrams silently drift from what the system actually does.

## Tool comparison, if the user asks about alternatives to PlantUML

This skill is scoped to PlantUML — don't switch formats unprompted. If a user asks whether
something else would fit better, the honest tradeoffs:

- **Mermaid** — natively rendered by GitHub, GitLab, and Notion; concise, Markdown-native
  syntax. Weaker layout control than PlantUML and a still-experimental C4 mode. Best for a
  diagram that lives in a GitHub PR/README and has a short half-life.
- **Structurizr DSL** — model-based: define elements/relationships once, generate multiple
  synchronized C4 views, with model (content) cleanly separated from views (presentation).
  Exports to PlantUML/Mermaid via its CLI. Best for a long-lived, multi-team reference
  architecture where several C4 views need to stay consistent with each other.
- **D2** — modern syntax with the strongest auto-layout of the code-first diagram tools.
  Renders natively on none of GitHub/GitLab/Notion and needs its own build step. Best when you
  fully control the docs pipeline and want the least manual layout tweaking.

A reasonable split for one organization: Mermaid for anything read directly in a GitHub PR;
C4-PlantUML (this skill) for CI-rendered architecture documentation; Structurizr DSL if/when
you outgrow keeping several hand-authored C4-PlantUML files in sync with each other.
