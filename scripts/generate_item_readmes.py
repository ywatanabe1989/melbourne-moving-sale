#!/usr/bin/env python3
"""Generate individual README.md for each item in images/items/<ID>/."""

from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "data" / "items.yaml"
IMAGES_DIR = BASE_DIR / "images" / "items"


def load_data():
    with open(DATA_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def generate_price_chart(item):
    """Generate ASCII step chart from price_aud_{jan,feb,mar}."""
    p_jan = item.get("price_aud_jan")
    p_feb = item.get("price_aud_feb")
    p_mar = item.get("price_aud_mar")

    # Build list of (month, price) tuples with valid prices
    entries = []
    if p_jan is not None:
        entries.append(("Jan", p_jan))
    if p_feb is not None:
        entries.append(("Feb", p_feb))
    if p_mar is not None:
        entries.append(("Mar", p_mar))

    if not entries:
        return ""

    lines = ["## 価格チャート（受け取り時期による）", "", "```"]
    lines.append("価格(AUD)")
    lines.append("    │")

    max_price = max(p for _, p in entries)

    for month, price in entries:
        bar_len = int((price / max_price) * 10) if max_price > 0 else 0
        lines.append(f"${price:>3} ┤{'■' * bar_len:<10}  ← {month}")
        lines.append("    │")

    lines.append("    └──────────────────")
    lines.append("```")
    lines.append("")
    lines.append("- 早め引取 → 高め（まだ使用中のため）")
    lines.append("- 遅め引取 → 安め（引越し直前で急ぎ処分）")
    lines.append("- まとめ買い → さらに割引")

    return "\n" + "\n".join(lines) + "\n"


def get_price_range(item):
    """Get min/max price from price_aud_{jan,feb,mar}."""
    prices = [
        item.get("price_aud_jan"),
        item.get("price_aud_feb"),
        item.get("price_aud_mar"),
    ]
    prices = [p for p in prices if p is not None]
    if prices:
        return min(prices), max(prices)
    return 0, 0


def format_reference_urls(urls):
    """Format reference URLs as markdown list."""
    if not urls:
        return "- -"
    return "\n".join(f"- {url}" for url in urls)


def generate_item_readme(item, meta):
    p_min, p_max = get_price_range(item)
    price_str = (
        item["notes"]
        if item.get("notes") and "$" in item["notes"]
        else f"${p_min}–{p_max}"
    )

    status_emoji = {
        "available": "🟢 Available",
        "reserved": "🟡 Reserved",
        "sold": "🔴 Sold",
    }.get(item["status"], item["status"])

    price_chart = generate_price_chart(item)

    # Format market value
    market_value = item.get("market_value")
    market_value_str = f"${market_value} AUD" if market_value else "-"

    # Format reference URLs
    ref_urls = format_reference_urls(item.get("reference_urls", []))

    readme = f"""# [{item["id"]}] {item["name"]}

**Status: {status_emoji}**

## 商品情報 / Item Info

| 項目 | 内容 | Field | Value |
|------|------|-------|-------|
| ID | {item["id"]} | ID | {item["id"]} |
| カテゴリ | {item["category"]} | Category | {item.get("category_en", item["category"])} |
| 状態 | {item["condition"]} | Condition | {item["condition"]} |
| 購入日 | {item["purchase_date"]} | Purchased | {item["purchase_date"]} |
| 数量 | {item["qty"]} | Qty | {item["qty"]} |
| 価格目安 | {price_str} AUD | Price Range | {price_str} AUD |
| 市場価格 | {market_value_str} | Market Value | {market_value_str} |

## 商品説明 / Description

**日本語:** {item["description"]}

**English:** {item.get("description_en", "")}
{price_chart}
## 写真 / Photos

<!-- このフォルダに写真を追加してください -->
<!-- Add photos to this folder -->

## リンク / Links

- 購入証明 / Proof: {item.get("proof_url") or "-"}
- 購入リンク / Product: {item.get("bought_url") or "-"}

### 参考リンク / Reference URLs

{ref_urls}

## 連絡先 / Contact

興味がある方はご連絡ください（優先順）:
1. **GitHub Issues** (preferred)
2. Reply (Facebookこの投稿への返信)
3. DM (Facebook)
4. Email: {meta["contact"]["email"]}
5. SMS: {meta["contact"]["phone"]}

{meta["contact"].get("name", "")}

---

受け渡し場所: {meta["location"]}周辺（〜{meta["deadline"]}）

[← 一覧に戻る](../../../README.md)
"""
    return readme


def main():
    data = load_data()
    meta = data["metadata"]
    items = data["items"]

    for item in items:
        item_dir = IMAGES_DIR / item["id"]
        item_dir.mkdir(parents=True, exist_ok=True)

        readme_path = item_dir / "README.md"
        readme_content = generate_item_readme(item, meta)

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)

        print(f"Created: {readme_path}")

    print(f"\nTotal: {len(items)} item READMEs created.")


if __name__ == "__main__":
    main()
