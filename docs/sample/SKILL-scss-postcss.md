# SKILL: SCSS Parsing with PostCSS

## Application Role
Presentational layer only. SCSS defines visual appearance compiled to static CSS at build time. Carries no business logic, no state mutations, no runtime execution. In SME queries about business logic or data flow, SCSS nodes are low-weight. In queries about UI appearance or component styling, SCSS nodes are high-weight.

## Tool
- postcss
- postcss-scss

## Install
```bash
npm install postcss postcss-scss
```

## Chunk Types
| Chunk Type | Description |
|---|---|
| variable | $name: value declarations |
| mixin | @mixin blocks — reusable style functions |
| style-rule | .class, #id, element selectors |
| import | @import statements |
| extend | @extend references |

## Edge Types
| Edge Type | Confidence | Description |
|---|---|---|
| IMPORTS | deterministic | @import → target .scss file |
| INCLUDES | deterministic | @include → mixin definition in same or imported file |
| EXTENDS | deterministic | @extend → source style-rule |
| STYLES | probabilistic | style-rule class name → matching JSX/HTML component |

## Known Limitations
- STYLES edge to components is probabilistic — class name string matched against component markup, not compiled
- Dynamic class names (JS-computed) are unresolvable
- CSS Modules scoped names may not match raw class names

## Parser Script
```javascript
const postcss = require('postcss');
const postcssScss = require('postcss-scss');
const fs = require('fs');
const { v4: uuidv4 } = require('uuid');

function parseScss(filePath) {
  const source = fs.readFileSync(filePath, 'utf8');
  const root = postcss.parse(source, { syntax: postcssScss });
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
        raw_cleaned: `@mixin ${node.params} { ${node.nodes.map(n => n.toString()).join(' ')} }`,
        edges: []
      });
    }

    // Imports
    if (node.type === 'atrule' && node.name === 'import') {
      nodes.push({
        node_id: uuidv4(),
        language: 'scss',
        source_file: filePath,
        chunk_type: 'import',
        raw_cleaned: `@import ${node.params}`,
        edges: [{
          type: 'IMPORTS',
          target_node_id: node.params.replace(/['"]/g, ''),
          confidence: 'deterministic'
        }]
      });
    }

    // Style rules
    if (node.type === 'rule') {
      const edges = [];

      node.walk(child => {
        if (child.type === 'atrule' && child.name === 'include') {
          edges.push({
            type: 'INCLUDES',
            target_node_id: child.params,
            confidence: 'deterministic'
          });
        }
        if (child.type === 'atrule' && child.name === 'extend') {
          edges.push({
            type: 'EXTENDS',
            target_node_id: child.params,
            confidence: 'deterministic'
          });
        }
      });

      // Probabilistic STYLES edge — class name to component
      const className = node.selector.replace(/^\./, '').split(':')[0].trim();
      if (className) {
        edges.push({
          type: 'STYLES',
          target_node_id: className,
          confidence: 'probabilistic'
        });
      }

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
