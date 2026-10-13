# MazeModel JSON and grid formats

All maze geometry uses source coordinates (normally pixels); `scale` is **millimeters per source unit**. To represent a millimeter drawing directly use scale1. The simulator uses graph edge polylines as the physical line geometry. IDs must be unique strings; nodes and referenced edge endpoints must exist.

```json
{
  "id":"custom-maze",
  "name":"My maze",
  "width":700,
  "height":520,
  "lineWidth":14,
  "scale":1,
  "heading":0,
  "start":"S",
  "finish":"F",
  "verified":false,
  "sourceType":"json",
  "warnings":[],
  "graph":{
    "nodes":[
      {"id":"S","x":80,"y":280},
      {"id":"A","x":230,"y":280},
      {"id":"D","x":230,"y":120},
      {"id":"F","x":620,"y":280}
    ],
    "edges":[
      {"id":"0","a":"S","b":"A","points":[{"x":80,"y":280},{"x":230,"y":280}]},
      {"id":"1","a":"A","b":"D","points":[{"x":230,"y":280},{"x":230,"y":120}]},
      {"id":"2","a":"A","b":"F","points":[{"x":230,"y":280},{"x":620,"y":280}]}
    ]
  }
}
```

Heading: East0°,South90°,West180°,North−90°. Screen y increases downwards. The first edge point is at node `a`, last at `b`; intermediate points retain curve shape. Crossings are connected **only if represented by a shared node**. A visual crossing without a common node does not create a graph connection.

Import also accepts top-level `nodes`/`edges`, or `intersections`/`segments` in the same node/edge format. It does not invent endpoints for unspecified segments. In importer-generated models, `segments`, `intersections` and `centerline` are derived convenience fields; `graph` remains the primary editable representation. Length is computed from polyline geometry. Raster imports include base64 PNG previews and possible endpoint gaps. JSON export includes them for repeatable inspection.

CSV grid:

```csv
1,1,1,1,1
1,S,0,0,1
1,0,1,0,1
1,0,0,F,1
1,1,1,1,1
```

TXT can contain the same CSV or compact rows like `1S001`. Grid must be rectangular. Default1wall,0open; S/F are special markers. Configurable open/wall values are normalized before parsing. JSON `{"grid":[[1,1,1],[1,"S","F"],[1,1,1]]}` is also accepted using default values.

Grid open-cell centers become nodes, adjacent open cells become edges. Cells are spaced40source units. Adjust scale and line width to match a physical line track. These are corridor centerlines, not a wall-clearance simulator.

Raster extraction removes tiny components, skeletonizes foreground, suppresses diagonal shortcut connections, clusters neighboring branch pixels, and follows skeleton chains into polylines. It retains disconnected components. Closed loops receive an anchor node rather than silently disappearing. For unusual diagrams, manually verify every connection.
