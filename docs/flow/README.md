# Workflow flow map

A live visual of how a video moves through the whole system: the 3 lines, the
pipeline stages A to C, and (the important part) the **ground layer vs template
layer** inside `/create-ads`, plus where each base rule is enforced.

## Run it
```bash
docs/flow/serve.sh          # then open http://localhost:8777/
```
The page polls `flow.json` every 1.5s, so **editing `flow.json` updates the page
live**. The model is the single source of truth; `index.html` just renders it.

## What it shows
- **Ground layer** (green): the steps every video goes through, identical for every
  template. Understand the footage, build the coherent script, apply the base rules.
- **Template layer** (amber): the only thing that changes per style. Same script,
  different visual outcome.
- **Gates** (blue): plan-check, frame check, director. `plan-check` is the shared
  gate every template passes through.
- **Enforcement tags** on each base rule: `plan-check` (mechanically enforced),
  `planner` (relies on judgement), `partial`, or `NOT ENFORCED` (red = the leak).

## Editing the model
`flow.json` fields: `lines`, `pipeline[].skills[]`, `createads.ground/template`,
`gates`, `knowledge`. Change any of it and watch the page redraw. This is our shared
canvas for redesigning the base layer.
