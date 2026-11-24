"""Compare keyword, embedding and hybrid retrieval on the support catalog with a learned model.

    pip install sentence-transformers
    python labs/support-kb/embed_eval.py --out labs/support-kb/embed-results.json

The default model is an open multilingual sentence encoder, so the run needs no API key.
The 36 queries were written for this lab: three per article in English, Roman Urdu and Urdu.
"""
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
# Same four articles and keyword terms as catalog.sql.
ARTICLES = {
    "receipts": ("Receipts and invoices. Open Trips, select your booking, then choose Receipts.", {"receipt", "invoice", "rasid", "رسید"}),
    "hours": ("Support desk opening hours. The support desk is open from 09:00 to 17:00 UTC.", {"hours", "schedule", "waqt", "اوقات"}),
    "itinerary": ("Trip itinerary and tickets. Open Trips and choose your booking to view its itinerary.", {"itinerary", "confirmation", "ticket", "ٹکٹ"}),
    "account": ("Account and profile settings. Open Settings and choose Account.", {"account", "profile", "settings"}),
}
QUERIES = {
    "receipts": {
        "en": ["Where can I get my invoice?", "I need a receipt for my booking", "How do I download proof of payment?"],
        "ur-Latn": ["Mujhe rasid chahiye", "Payment ka bill kahan milay ga?", "Booking ki rasid download karni hai"],
        "ur": ["مجھے رسید چاہیے", "ادائیگی کا بل کہاں ملے گا؟", "بکنگ کی رسید ڈاؤن لوڈ کرنی ہے"],
    },
    "hours": {
        "en": ["When is the support desk open?", "What are your opening times?", "What time do you close?"],
        "ur-Latn": ["Desk kab khulta hai?", "Support ka waqt kya hai?", "Aap kab tak available hain?"],
        "ur": ["دفتر کب کھلتا ہے؟", "سپورٹ کے اوقات کیا ہیں؟", "آپ کب تک دستیاب ہیں؟"],
    },
    "itinerary": {
        "en": ["Show me my trip details", "Where is my booking confirmation?", "I can't find my ticket"],
        "ur-Latn": ["Mera ticket kahan hai?", "Safar ki tafseel dekhni hai", "Booking confirmation nahi mil rahi"],
        "ur": ["میرا ٹکٹ کہاں ہے؟", "سفر کی تفصیل دیکھنی ہے", "بکنگ کی تصدیق نہیں مل رہی"],
    },
    "account": {
        "en": ["How do I update my profile?", "Change my account settings", "Where do I edit my name?"],
        "ur-Latn": ["Profile kaise update karun?", "Account ki settings badalni hain", "Apna naam kahan tabdeel karun?"],
        "ur": ["پروفائل کیسے اپ ڈیٹ کروں؟", "اکاؤنٹ کی سیٹنگز بدلنی ہیں", "اپنا نام کہاں تبدیل کروں؟"],
    },
}


def keyword(query):
    """Top article by term overlap; a tie or no overlap returns nothing, as in agent.py."""
    words = set(re.findall(r"[^\W_]+", query.casefold()))
    ranked = sorted(((len(words & terms), slug) for slug, (_, terms) in ARTICLES.items()), reverse=True)
    return ranked[0][1] if ranked[0][0] > ranked[1][0] else None


def load_encoder(name):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(name)
    return lambda texts: model.encode(texts, normalize_embeddings=True).tolist()


def evaluate(encode):
    slugs = list(ARTICLES)
    docs = encode([ARTICLES[slug][0] for slug in slugs])
    rows = [(expected, language, query) for expected, by_language in QUERIES.items()
            for language, queries in by_language.items() for query in queries]
    vectors = encode([query for _, _, query in rows])
    tally = {language: {"keyword": 0, "embedding": 0, "hybrid": 0, "total": 0} for language in ("en", "ur-Latn", "ur")}
    misses = []
    for (expected, language, query), vector in zip(rows, vectors):
        scores = [sum(a * b for a, b in zip(vector, doc)) for doc in docs]
        by_vector = slugs[scores.index(max(scores))]
        by_keyword = keyword(query)
        picks = {"keyword": by_keyword, "embedding": by_vector, "hybrid": by_keyword or by_vector}
        tally[language]["total"] += 1
        for method, pick in picks.items():
            tally[language][method] += pick == expected
        if picks["embedding"] != expected or picks["hybrid"] != expected:
            misses.append({"query": query, "language": language, "expected": expected, **picks})
    overall = {method: sum(tally[language][method] for language in tally) for method in ("keyword", "embedding", "hybrid", "total")}
    return {"overall": overall, "by_language": tally, "misses": misses}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = {"utc": datetime.now(timezone.utc).isoformat(), "model": args.model, **evaluate(load_encoder(args.model))}
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
