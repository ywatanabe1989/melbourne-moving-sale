#!/usr/bin/env python3
"""
Sync items.yaml to README.md, GitHub Issues, and CSV.

Usage:
    python sync.py readme      # Update README.md from YAML
    python sync.py issues      # Sync GitHub Issues from YAML
    python sync.py csv         # Export to CSV
    python sync.py all         # Do all of the above
"""

import csv
import subprocess
import sys
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "data" / "items.yaml"
README_FILE = BASE_DIR / "README.md"
CSV_FILE = BASE_DIR / "data" / "items.csv"
REPO = "ywatanabe1989/melbourne-moving-sale"


def load_data():
    """Load items from YAML file."""
    with open(DATA_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


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


def save_data(data):
    """Save items to YAML file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        yaml.dump(
            data, f, allow_unicode=True, default_flow_style=False, sort_keys=False
        )


def generate_readme(data):
    """Generate README.md from YAML data."""
    from collections import OrderedDict

    meta = data["metadata"]
    items = data["items"]

    # Group items by category (preserve order of first appearance)
    categories = OrderedDict()
    for item in items:
        cat = item["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)

    def get_monthly_prices(item):
        """Get prices for Jan, Feb, Mar from price_aud_{jan,feb,mar}."""
        jan = item.get("price_aud_jan")
        feb = item.get("price_aud_feb")
        mar = item.get("price_aud_mar")
        return {
            "Jan": str(jan) if jan is not None else "NA",
            "Feb": str(feb) if feb is not None else "NA",
            "Mar": str(mar) if mar is not None else "NA",
        }

    def format_row_html(item, show_category=True):
        status_icon = {"available": "", "reserved": "[予約済]", "sold": "[売却済]"}.get(
            item["status"], ""
        )
        buy = (
            f'<a href="{item["bought_url"]}">参考</a>'
            if item.get("bought_url")
            else "-"
        )
        issue_link = (
            f'<a href="https://github.com/{REPO}/issues/{item["issue_number"]}">#{item["issue_number"]}</a>'
            if item.get("issue_number")
            else "-"
        )
        prices = get_monthly_prices(item)
        if show_category:
            return f"<tr><td>{item['id']}</td><td>{item['category']}</td><td>{status_icon}{item['name']}</td><td>{item['condition']}</td><td>{item['qty']}</td><td>{prices['Jan']}</td><td>{prices['Feb']}</td><td>{prices['Mar']}</td><td>{buy}</td><td>{issue_link}</td></tr>"
        else:
            return f"<tr><td>{item['id']}</td><td>{status_icon}{item['name']}</td><td>{item['condition']}</td><td>{item['qty']}</td><td>{prices['Jan']}</td><td>{prices['Feb']}</td><td>{prices['Mar']}</td><td>{buy}</td><td>{issue_link}</td></tr>"

    def make_html_table(items, show_category=True):
        if show_category:
            header = """<div style="overflow-x: auto;">
<table>
<thead>
<tr><th>ID</th><th>カテゴリ</th><th>品目</th><th>状態</th><th>数量</th><th>Jan (AUD)</th><th>Feb (AUD)</th><th>Mar (AUD)</th><th>参考</th><th>Issue</th></tr>
</thead>
<tbody>
"""
        else:
            header = """<div style="overflow-x: auto;">
<table>
<thead>
<tr><th>ID</th><th>品目</th><th>状態</th><th>数量</th><th>Jan (AUD)</th><th>Feb (AUD)</th><th>Mar (AUD)</th><th>参考</th><th>Issue</th></tr>
</thead>
<tbody>
"""
        rows = "\n".join(format_row_html(item, show_category) for item in items)
        footer = """</tbody>
</table>
</div>"""
        return header + rows + footer

    readme = f"""<!-- ---
!-- Timestamp: Auto-generated
!-- Author: ywatanabe
!-- File: /home/ywatanabe/proj/melbourne-moving-sale/README.md
!-- --- -->

<!-- ID Format: <category>-<item-name> -->

# 【{meta["title"]}】{meta["subtitle"]}

メルボルン在住の皆さま、はじめまして。突然の投稿失礼いたします。

このたび {meta["deadline"]} に帰国予定 のため、現在使用している家具・家電類をお譲りできる方を探しております。
ご興味ある方は DM いただけますと幸いです（まとめ買い歓迎・価格相談OK）。

---

## お譲りできるもの

価格は受け取り時期により変動します（早め＝高め、遅め＝安め）。まとめ買い割引あり。

"""

    # Generate sections for each category (sorted by price descending)
    def get_max_price(item):
        prices = [
            item.get("price_aud_jan"),
            item.get("price_aud_feb"),
            item.get("price_aud_mar"),
        ]
        prices = [p for p in prices if p is not None]
        return max(prices) if prices else 0

    for cat_name, cat_items in categories.items():
        cat_en = cat_items[0].get("category_en", cat_name)
        # Sort items by max price (descending)
        sorted_items = sorted(cat_items, key=get_max_price, reverse=True)
        readme += f"\n### {cat_name} / {cat_en}\n\n"
        readme += make_html_table(sorted_items, show_category=False)
        readme += "\n"

    readme += f"""
---

## 住居情報（希望者のみ）

{meta["location"]} で長期で住んでいる物件の ホスト紹介が可能 です。
空室状況・条件はホスト次第なので、興味ある方はDMください（条件交渉や契約は各自の責任でお願いします）。

---

## 5) 受け渡し

- 場所: {meta["location"]} 周辺（詳細はDM）
- 受け渡し時期: 〜{meta["deadline"]}（相談）
- まとめ買い・早め引き取りの方は優先しやすいです
- 一部まだ使用中の物もあるため、引き取り時期が遅めでも問題ない方は お値引き可能 です

### 受け渡し方法 / Delivery Options

1. **Direct pickup** - 直接引き取り（Maidstone周辺）
2. **Australia Post** - 郵送対応可（送料別）
3. **AirTasker** - 配送代行（事故等の保証なし）

---

なお、Facebookは最近新しく作成したアカウントのため不安に思われるかもしれませんが、誠実に対応いたします。
どうぞよろしくお願いいたします。

---

## アイテム数まとめ

- カテゴリ数: {len(categories)}
- 合計: {len(items)}品目

すべてAmazon購入履歴から購入証明を提示できます。

DMでお気軽にご連絡ください。

---

## 注意事項 / Disclaimer

- **価格交渉歓迎** / Negotiation welcome
- **写真は問い合わせ時に撮影** / Photos will be taken on request
- このリストはAIを使用して作成されており、著者がすべての情報を確認していないため、誤った情報が含まれている可能性があります
- This list was created using AI and the author has not confirmed all information yet, so wrong information might be included
- **購入前に必要な確認を行います** / Necessary checks will be performed before purchase
- 誤りがあれば修正いたします / Wrong information will be corrected

---

## Contact
ご連絡は: GitHub Issues (優先) / [Facebook](https://www.facebook.com/profile.php?id=61586061710421) / Email: {meta["contact"]["email"]} / SMS: {meta["contact"]["phone"]}

{meta["contact"].get("name", "")}
<!-- EOF -->
"""

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(readme)

    print(f"README.md updated with {len(items)} items.")


def sync_issues(data):
    """Sync GitHub Issues from YAML data."""
    items = data["items"]
    meta = data["metadata"]

    # Create labels first
    categories = list(set(item["category"] for item in items))
    colors = [
        "0052CC",
        "1D76DB",
        "5319E7",
        "0E8A16",
        "D93F0B",
        "FBCA04",
        "B60205",
        "006B75",
        "1D1D1D",
        "C5DEF5",
        "BFD4F2",
        "D4C5F9",
        "FEF2C0",
        "F9D0C4",
        "C2E0C6",
        "E99695",
    ]

    print("Creating labels...")
    for i, cat in enumerate(categories):
        color = colors[i % len(colors)]
        subprocess.run(
            ["gh", "label", "create", cat, "--color", color, "--repo", REPO],
            capture_output=True,
        )

    # Status labels
    subprocess.run(
        [
            "gh",
            "label",
            "create",
            "available",
            "--color",
            "0E8A16",
            "--description",
            "Available for sale",
            "--repo",
            REPO,
        ],
        capture_output=True,
    )
    subprocess.run(
        [
            "gh",
            "label",
            "create",
            "reserved",
            "--color",
            "FBCA04",
            "--description",
            "Reserved",
            "--repo",
            REPO,
        ],
        capture_output=True,
    )
    subprocess.run(
        [
            "gh",
            "label",
            "create",
            "sold",
            "--color",
            "B60205",
            "--description",
            "Sold",
            "--repo",
            REPO,
        ],
        capture_output=True,
    )

    print("Creating/updating issues...")
    updated_items = []
    for item in items:
        # Get monthly prices
        jan = item.get("price_aud_jan")
        feb = item.get("price_aud_feb")
        mar = item.get("price_aud_mar")
        prices = {
            "Jan": str(jan) if jan is not None else "NA",
            "Feb": str(feb) if feb is not None else "NA",
            "Mar": str(mar) if mar is not None else "NA",
        }

        # Format reference URLs
        ref_urls = item.get("reference_urls", [])
        ref_section = ""
        if ref_urls:
            ref_lines = []
            for ref in ref_urls:
                if isinstance(ref, dict):
                    ref_lines.append(
                        f"- [{ref.get('store', 'Link')}]({ref.get('url', '')}) - {ref.get('price', '')} {ref.get('currency', '')}"
                    )
                else:
                    ref_lines.append(f"- {ref}")
            ref_section = "\n".join(ref_lines)
        else:
            ref_section = "- -"

        # Notes section (if exists)
        notes_section = (
            f"\n## 備考 / Notes\n\n{item['notes']}\n" if item.get("notes") else ""
        )

        body = f"""## 商品情報 / Item Info

| 項目 | 内容 |
|------|------|
| **ID** | {item["id"]} |
| **カテゴリ** | {item["category"]} / {item.get("category_en", "")} |
| **状態** | {item["condition"]} |
| **購入日** | {item["purchase_date"]} |
| **数量** | {item["qty"]} |
| **市場価格** | {item.get("market_value", "-")} AUD |

## 価格 / Prices (AUD)

| Jan | Feb | Mar |
|-----|-----|-----|
| {prices["Jan"]} | {prices["Feb"]} | {prices["Mar"]} |
{notes_section}
## 商品説明 / Description

**日本語:** {item["description"]}

**English:** {item.get("description_en", "")}

## 写真 / Photos

<!-- 写真を追加してください -->

## 参考リンク / Reference URLs

{ref_section}

## 連絡先 / Contact

興味がある方はご連絡ください（優先順）:
1. **GitHub Issues** (preferred)
2. Reply (Facebookこの投稿への返信)
3. DM (Facebook)
4. Email: {meta["contact"]["email"]}
5. SMS: {meta["contact"]["phone"]}

{meta["contact"].get("name", "")}

---
受け渡し場所: {meta["location"]}周辺
"""

        title = f"[{item['id']}] {item['name']}"

        if item.get("issue_number"):
            # Update existing issue
            print(f"  Updating issue #{item['issue_number']}: {item['name']}")
            subprocess.run(
                [
                    "gh",
                    "issue",
                    "edit",
                    str(item["issue_number"]),
                    "--repo",
                    REPO,
                    "--title",
                    title,
                    "--body",
                    body,
                ],
                capture_output=True,
            )
        else:
            # Create new issue
            print(f"  Creating issue: {item['name']}")
            result = subprocess.run(
                [
                    "gh",
                    "issue",
                    "create",
                    "--repo",
                    REPO,
                    "--title",
                    title,
                    "--body",
                    body,
                    "--label",
                    item["category"],
                    "--label",
                    item["status"],
                ],
                capture_output=True,
                text=True,
            )

            # Extract issue number from URL
            if result.returncode == 0:
                url = result.stdout.strip()
                issue_num = url.split("/")[-1]
                item["issue_number"] = int(issue_num)
                print(f"    Created: #{issue_num}")

        updated_items.append(item)

    # Save updated data with issue numbers
    data["items"] = updated_items
    save_data(data)
    print(f"Issues synced. Updated {len(updated_items)} items in YAML.")


def export_csv(data):
    """Export items to CSV."""
    items = data["items"]

    fieldnames = [
        "id",
        "category",
        "category_en",
        "name",
        "name_en",
        "condition",
        "purchase_date",
        "qty",
        "price_aud_jan",
        "price_aud_feb",
        "price_aud_mar",
        "market_value",
        "status",
        "proof_url",
        "bought_url",
        "description",
        "description_en",
        "issue_number",
        "notes",
    ]

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for item in items:
            writer.writerow(item)

    print(f"Exported {len(items)} items to {CSV_FILE}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    data = load_data()

    if command == "readme":
        generate_readme(data)
    elif command == "issues":
        sync_issues(data)
    elif command == "csv":
        export_csv(data)
    elif command == "all":
        generate_readme(data)
        sync_issues(data)
        export_csv(data)
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
