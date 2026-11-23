# Creative approval prototype

This offline prototype renders an approved fictional campaign brief into a
self-contained HTML asset. It validates palette syntax, escapes supplied copy,
and blocks three claim phrases before export. The approval field is a manual
demo input. It does not record an authenticated reviewer.

Run from the repository root with an unused output path:

    python labs/creative-flow/build.py labs/creative-flow/brief.json /tmp/northline-card.html

Open the generated card in a browser. Change review_status to pending and run
again to verify the export gate. Add a prohibited claim to exercise the brand
check. The original brief is already marked approved as a reproducible fixture.

This starter covers brief validation, a manual review gate and HTML export.
The n8n workflow, image generation, design-tool export and demo video are open.

## n8n and layered export

Import workflow.json into n8n and run it manually. The embedded fictional
brief starts in pending review. Inspect the returned draft. After human review,
update the review decision in the brief node to approved and rerun to get
the HTML export in the final node output. The workflow does not invoke a
paid image provider. It uses the supplied copy and a typography-first layout.

The workflow Code node passed four Node checks covering pending and approved
outputs, invalid palette and prohibited claims. Import and execution in a
running n8n instance were not tested here.

The static Photoshop sample contains separate background and raster text
layers. Decode it with `base64 -d demo.psd.b64 > demo.psd` on Linux, or
`base64 -D -i demo.psd.b64 -o demo.psd` on macOS. ImageMagick confirmed
the composite and two layers. The live HTML output is shown in example.html.
The PSD sample is a separate static design handoff.
