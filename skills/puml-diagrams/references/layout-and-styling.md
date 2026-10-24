# Preprocessor Directives, Layout Control, and Styling

Read this file before writing shared includes/themes, before fighting with layout on a large
diagram, or before deciding between `skinparam` and the newer `<style>` block.

## Preprocessor directives

- `!include file.iuml` — include a file; by default a given file is included only once per
  render even if referenced multiple times.
- `!include_once` — include, and raise an error if the same file is included more than once
  (catches accidental duplicate includes).
- `!include_many` — explicitly allow a file to be included multiple times.
- `!include foo.puml!1` or `!include foo.puml!MY_ID` — include one specific
  `@startuml(id=MY_ID)` block out of a file that defines several.
- `!includesub file.puml!BASIC` — include only a named subsection of a file, marked with
  `!startsub BASIC` / `!endsub` inside the source file. Useful for pulling one fragment of a
  larger reference diagram into several smaller ones without duplicating source.
- `!theme <name>` — apply a bundled or custom theme. Custom theme files follow the naming
  convention `puml-theme-<name>.puml` and can be loaded from a local folder or a URL with
  `!theme <name> from <path/URL>`.
- **Reusable logic:** use `!function`, `!procedure`, and `!$variables` for anything that needs
  parameters or repetition. Do **not** use `!define`/`!definelong` for new work — the PlantUML
  docs mark these as legacy in favor of the function/procedure forms.

## `skinparam` vs. `<style>`

PlantUML now supports a CSS-like `<style>...</style>` block (inline, or via
`<style file=MyOwnFile.css>`) with element/stereotype/`.class` selectors and cascading —
functionally closer to real CSS than `skinparam` ever was. The docs describe `skinparam` as
"being phased out" in favor of `<style>`, while guaranteeing existing `skinparam`-based diagrams
keep working; this is a migration in progress, not a hard deprecation with a removal date.

**Practical recommendation:** default to `skinparam` in a shared `.iuml` include for now — it
remains the most broadly compatible option across GitLab's PlantUML server, Confluence
rendering apps, IDE extensions, and older pinned CI versions. Adopt `<style>` selectively where
you control the exact PlantUML version end-to-end (e.g., a single CI-rendered pipeline with no
external renderer in the loop) and want its more powerful selector/cascade model.

When using `skinparam` with stereotypes, always pair `BackgroundColor` with an explicit
`FontColor` — an unpaired background color is a common source of unreadable low-contrast text
that only shows up once rendered, not while editing the source.

## Layout control

PlantUML hands node/arc layout to Graphviz for most diagram types (see the main skill file for
which types need it). Graphviz's layout quality degrades with edge crossings and non-planar
graphs — the practitioner-recommended fix, ahead of any of the techniques below, is **splitting
the diagram**; layout tweaking time grows faster than linearly with element count. Once a
diagram is appropriately scoped, these controls help:

- **`left to right direction`** flips the default top-to-bottom flow — often clearer for wide,
  shallow structures (a request flowing through a small number of services).
- **Declaration order drives ranking.** Declare elements and links in the order you want them
  to visually flow ("top down" in the source), or the diagram can flip in an unintuitive way.
- **Directional links** — `-up->`, `-down->`, `-left->`, `-right->` (and their shortcuts) —
  place one element relative to another explicitly instead of trusting the automatic layout.
- **`A -[hidden]- B`** creates an invisible link purely to influence placement, with no visual
  line. Repeat it to pull two elements closer together than the automatic layout would.
- **`A -[norank]- B`** excludes a link from rank computation — use when a relationship exists
  logically but shouldn't affect vertical/horizontal ordering.
- **`together { ... }`** keeps a group of elements clustered regardless of their relationships
  to elements outside the group.
- **`skinparam nodesep`/`ranksep`** tune spacing between nodes and between ranks.
- **`skinparam linetype ortho`** or **`linetype polyline`** change edge routing style — `ortho`
  in particular produces much cleaner output for ER/crow's-foot diagrams (see the main skill
  file's ER Diagrams section).

## Alternative layout engines (avoiding or replacing Graphviz)

- **Smetana** (`!pragma layout smetana`) — a pure-Java port of Graphviz's layout algorithm,
  meaning no external `dot` binary is required at all. Available experimentally since PlantUML
  1.2021.5, for the diagram types that support it. Reach for this when the render environment
  can't or shouldn't install Graphviz (e.g., a locked-down CI image), not as a general
  layout-quality upgrade.
- **ELK** (`!pragma layout elk`) — a different layout engine, usable since roughly the same
  PlantUML version and bundled directly in the PlantUML jar since 1.2024.6 (no separate
  `elk-full.jar` needed anymore). PlantUML's own docs still describe it as "really an
  alpha-version" — treat it as worth trying on a diagram where Graphviz's output is
  particularly bad, not as a default.

## Image size limit

PlantUML caps rendered image width/height at 4096px by default. For a diagram that's
legitimately large (and hasn't been split further), override it with the
`PLANTUML_LIMIT_SIZE` environment variable or `-D` flag, e.g. `-DPLANTUML_LIMIT_SIZE=8192`. If
you're hitting this limit regularly, treat it as a signal the diagram should be split rather
than just raising the cap — the underlying legibility problem doesn't go away because the image
got bigger.
