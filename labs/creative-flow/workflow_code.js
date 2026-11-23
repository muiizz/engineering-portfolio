// Export an HTML draft after checking the brief and explicit review decision.
const input = $input.first().json;
const required = ["brand", "headline", "copy", "background", "foreground"];
const escape = (s) => s.replace(/[&<>"']/g, (ch) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[ch]);

if (required.some((field) => typeof input[field] !== "string" || !input[field].trim())) {
  throw new Error("Missing brief field");
}
const palette = /^#[0-9a-f]{6}$/i;
if (!palette.test(input.background) || !palette.test(input.foreground)) {
  throw new Error("Invalid palette");
}
if (/\b(guaranteed|cure|clinically proven)\b/i.test([input.brand, input.headline, input.copy].join(" "))) {
  throw new Error("Unsupported claim requires editorial review");
}
const headline = escape(input.headline);
const brand = escape(input.brand);
const copy = escape(input.copy);
const draft = `<!doctype html><html lang="en"><meta charset="utf-8">
<title>${brand}</title><body style="background:${input.background};color:${input.foreground};padding:4rem;font-family:system-ui">
<p>${brand}</p><h1>${headline}</h1><p>${copy}</p></body></html>`;
if (input.review_status !== "approved") {
  return [{json: {status: "awaiting_review", draft}}];
}
return [{json: {status: "approved", filename: "campaign-card.html", asset: draft}}];
