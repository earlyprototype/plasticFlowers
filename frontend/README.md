# frontend

Next.js application for plasticFlower. Follow the MVP structure guide for module boundaries.

## Open an exported conversation

From the `frontend` directory, run `npm ci` and `npm run dev`. Visit
[the local viewer](http://localhost:3000/viewer), or choose **Open exported
conversation** on the home page. The frontend can run with the backend stopped.

Choose **Open JSON export** and select the file saved by the export panel's
**JSON** button. The viewer reads the file in the browser. Pan or zoom to
inspect flowers and hover over an edge to see its description. The panel
beside the graph shows the bundled transcript.

To try the viewer, open [rooftop-garden.json](fixtures/rooftop-garden.json).
The Rain collection and Rooftop garden flowers are joined by the “waters roots”
relationship from Rain barrel to Basil roots. The JSON exporter leaves
`graph.bridges` empty. The canvas identifies bridges from the flower
membership of the relationship's endpoints.

Each assigned node must appear exactly once in its flower's member list.
A supplied bridge must cite graph relationships that run from its source
flower to its target flower. If the JSON, a timestamp or a graph reference
is invalid, the viewer shows the error and keeps the previous graph and transcript.
Open [empty.json](fixtures/empty.json) to clear the graph and transcript.

## Offline browser regression

With the frontend dependencies and Chrome installed, run these commands from
`frontend`. The browser test starts its own local production frontend, blocks
service requests and takes the browser offline before selecting files.

```sh
npm run build
npm run test:viewer
```

To use an installed Microsoft Edge browser, set `CHROMIUM_CHANNEL` to
`msedge` before running the test. Run the parser and other frontend unit
tests with `npm test`.
