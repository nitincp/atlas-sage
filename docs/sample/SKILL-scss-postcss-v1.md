# SKILL: SCSS Parsing and Summarisation
**Version:** 1.0  
**Status:** Initial — pending validation  
**Tool:** postcss + postcss-scss

---

## Application Role
SCSS is a CSS preprocessor. Compiled to static CSS at build time. Never executed at runtime. Carries zero business logic and zero state mutations. Architecturally significant because it exposes what domain concepts the application considered important enough to style explicitly.

**Query weighting:**
- Skip SCSS nodes for: business logic, data flow, state mutation queries
- Prioritise SCSS nodes for: UI structure, component identity, domain concept visibility queries

---

## Install
```bash
npm install postcss postcss-scss uuid
```

---

## Chunk Types
| Chunk Type | Description |
|---|---|
| variable | $name: value — design token |
| mixin | @mixin block — reusable style function |
| style-rule | .class selector block |
| import | @import — file dependency |

---

## Edge Types
| Edge Type | Confidence | Description |
|---|---|---|
| IMPORTS | deterministic | @import → target .scss file |
| INCLUDES | deterministic | @include → mixin name |
| EXTENDS | deterministic | @extend → source class |
| STYLES | probabilistic | class name → matching component |

---

## Parser Script
```javascript
const postcss = require('postcss');
const postcssScss = require('postcss-scss');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

function parseScss(filePath) {
  const source = fs.readFileSync(filePath, 'utf8');
  const root = postcss().process(source, { 
    syntax: postcssScss, 
    from: filePath 
  }).root;
  const nodes = [];

  root.walk(node => {
    // Variables
    if (node.type === 'decl' && node.prop.startsWith('$')) {
      nodes.push({
        node_id: uuidv4(),
        language: 'scss',
        source_file: filePath,
        chunk_type: 'variable',
        raw_cleaned: `${node.prop}: ${node.value}`,
        edges: []
      });
    }

    // Mixins
    if (node.type === 'atrule' && node.name === 'mixin') {
      nodes.push({
        node_id: uuidv4(),
        language: 'scss',
        source_file: filePath,
        chunk_type: 'mixin',
        raw_cleaned: `@mixin ${node.params}`,
        edges: []
      });
    }

    // Imports
    if (node.type === 'atrule' && node.name === 'import') {
      const target = node.params.replace(/['"]/g, '');
      nodes.push({
        node_id: uuidv4(),
        language: 'scss',
        source_file: filePath,
        chunk_type: 'import',
        raw_cleaned: `@import ${node.params}`,
        edges: [{
          type: 'IMPORTS',
          target_node_id: target,
          confidence: 'deterministic'
        }]
      });
    }

    // Style rules (top-level only)
    if (node.type === 'rule' && node.parent.type === 'root') {
      const edges = [];
      node.walk(child => {
        if (child.type === 'atrule' && child.name === 'include')
          edges.push({ type: 'INCLUDES', target_node_id: child.params.split('(')[0].trim(), confidence: 'deterministic' });
        if (child.type === 'atrule' && child.name === 'extend')
          edges.push({ type: 'EXTENDS', target_node_id: child.params.trim(), confidence: 'deterministic' });
      });
      const sel = node.selector.replace(/^\./, '').split(/[:\s{]/)[0].trim();
      if (sel && sel !== '&' && sel !== '*')
        edges.push({ type: 'STYLES', target_node_id: sel, confidence: 'probabilistic' });

      nodes.push({
        node_id: uuidv4(),
        language: 'scss',
        source_file: filePath,
        chunk_type: 'style-rule',
        raw_cleaned: node.toString(),
        edges
      });
    }
  });

  return nodes;
}

module.exports = { parseScss };
```

---

## Summarisation Instructions

These instructions tell ATLAS how to generate a plain English summary for each chunk type. The summary goes into the vector store. It must capture domain meaning, not technical detail.

### variable chunk
Look at the variable name and value together.
- If name contains a domain word (brand, danger, success, primary, z-modal) — state what design decision it represents
- Group variables by prefix when summarising a file: brand colours, spacing scale, z-index layers
- Example: `$brand-danger: #D32F2F` → "Danger state colour used for errors, warnings, and destructive actions"

### mixin chunk
State what visual behaviour the mixin abstracts.
- If the mixin name implies layout (flex-center, flex-between) — describe the layout pattern
- If the mixin implies responsiveness (respond-to) — note it governs breakpoint behaviour
- If the mixin implies depth/elevation — note it governs visual layering
- Example: `@mixin elevation($level)` → "Controls shadow depth for visual layering. Three levels suggesting a consistent elevation system across the UI"

### style-rule chunk
This is the most important chunk for domain meaning.
- Read the class name as a domain concept first — .flight-card, .btn-danger, .app-header
- Look at BEM modifiers (--delayed, --selected, --cancelled) as domain states
- Note which mixins it includes — they tell you about layout and responsiveness
- Note which classes it extends — they tell you about inheritance hierarchy
- Note which brand variables it uses — they tell you about visual intent
- State what UI concept this rule represents and what states it exposes
- DO NOT describe CSS properties — describe what the rule means
- Example: `.flight-card__status--cancelled` → "Cancelled flight state. Uses danger colour with strikethrough — visually communicates both the negative status and the irreversibility of cancellation"

### import chunk
State the dependency relationship.
- Example: `@import 'variables'` → "Depends on the central design token file. Changes to brand colours or spacing propagate here automatically"

---

## Known Limitations
- BEM child elements (&__route, &__status) are nested and not extracted as separate top-level nodes in v1.0 — domain states within a component may be missed
- Dynamic class names computed in JavaScript are unresolvable
- STYLES edge is probabilistic — class name matched against component markup by string, not compiled reference
- Pseudo-selectors (&:hover, &:disabled) are not extracted as separate nodes

## Upgrade Triggers
- If BEM child elements carry significant domain meaning (status states, price display) → extract nested BEM elements as separate nodes
- If summarisation misses domain states visible in nested rules → update summarisation instructions for style-rule chunks
