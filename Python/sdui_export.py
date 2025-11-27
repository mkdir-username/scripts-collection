import requests
import json

# === CONFIGURATION ===
FIGMA_TOKEN = "***REMOVED***"  # ← Вставь сюда токен из Figma Settings → Personal Access Tokens
FILE_KEY = "j07vqGh7oUQbVlutjfGOiN"
NODE_ID = "8252-111605"

# === CONSTANTS ===
SPACING_MAP = {
    0: "zero",
    2: "xxxs",
    4: "xxs",
    6: "xs",
    8: "s",
    12: "m",
    16: "l",
    20: "xl",
    24: "xxl",
}


# === HELPERS ===
def get_spacing(px):
    if px is None:
        return "zero"
    px = float(px)
    closest = min(SPACING_MAP.keys(), key=lambda x: abs(x - px))
    return SPACING_MAP[closest]


def parse_layer_name(name):
    parts = name.split(":")
    type_ = parts[0].strip()
    variant = parts[1].strip() if len(parts) > 1 else None
    return type_, variant


def get_text_content(node):
    if node.get("type") == "TEXT":
        return node.get("characters", "")
    if "children" in node:
        for child in node["children"]:
            if child.get("type") == "TEXT" or "Label" in child.get("name", ""):
                return child.get("characters", "")
    return "Action"


# === CORE LOGIC ===
def transform_node(node):
    if node.get("visible") is False:
        return None

    name = node.get("name", "")
    node_type = node.get("type")
    sdui_type, variant = parse_layer_name(name)

    # StackView (Frame with AutoLayout)
    layout_mode = node.get("layoutMode")
    is_stack = "StackView" in sdui_type or (layout_mode in ["VERTICAL", "HORIZONTAL"])

    if is_stack and node_type in ["FRAME", "INSTANCE", "COMPONENT"]:
        children_raw = node.get("children", [])
        children = [transform_node(c) for c in children_raw]
        children = [c for c in children if c is not None]

        axis = "horizontal" if layout_mode == "HORIZONTAL" else "vertical"
        spacing = get_spacing(node.get("itemSpacing", 0))

        return {
            "type": "StackView",
            "content": {"axis": axis, "spacing": spacing, "children": children},
        }

    # LabelView
    if "LabelView" in sdui_type or node_type == "TEXT":
        text_val = node.get("characters", "Text")
        return {
            "type": "LabelView",
            "content": {
                "text": {"value": text_val},
                "style": variant if variant else "primary",
            },
        }

    # ButtonView V2
    if "ButtonView" in sdui_type:
        text_val = get_text_content(node)
        preset_map = {
            "primary": "primaryRectangleShape",
            "secondary": "secondaryRectangleShape",
            "clear": "clearRectangleShape",
        }
        preset = preset_map.get(variant, "primaryRectangleShape")

        return {
            "type": "ButtonView",
            "version": 2,
            "content": {
                "preset": preset,
                "textLabels": {
                    "title": {
                        "type": "LabelView",
                        "content": {"text": {"value": text_val}},
                    }
                },
            },
        }

    # IconView
    if "IconView" in sdui_type or node_type == "VECTOR":
        return {
            "type": "IconView",
            "content": {
                "image": {"type": "remote", "url": "https://placeholder.com/icon.png"},
                "size": variant if variant else "m",
            },
        }

    # Fallback: unwrap containers
    if "children" in node:
        children_raw = node.get("children", [])
        children = [transform_node(c) for c in children_raw]
        children = [c for c in children if c is not None]

        if len(children) == 1:
            return children[0]
        if len(children) > 1:
            return {
                "type": "StackView",
                "content": {"axis": "vertical", "children": children},
            }

    return None


# === RUNNER ===
def main():
    if not FIGMA_TOKEN:
        print("❌ Error: FIGMA_TOKEN не заполнен.")
        print(
            "👉 Получи токен: Figma → Settings → Personal Access Tokens → Create new token"
        )
        print("   Вставь в переменную FIGMA_TOKEN в начале скрипта.")
        return

    # API требует URL-кодирование двоеточия в node-id
    node_id_encoded = NODE_ID.replace("-", "%3A")
    url = f"https://api.figma.com/v1/files/{FILE_KEY}/nodes?ids={node_id_encoded}"
    headers = {"X-Figma-Token": FIGMA_TOKEN}

    print(f"🔍 Fetching node {NODE_ID}...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if response.status_code == 403:
            print("   Проверь: 1) Токен валиден, 2) Файл доступен для твоего аккаунта")
        return
    except Exception as e:
        print(f"❌ API Error: {e}")
        return

    # Навигация к документу
    try:
        # API может возвращать ключ в разных форматах: 8252:111605, 8252-111605, 8252%3A111605
        node_with_colon = NODE_ID.replace("-", ":")
        if node_id_encoded in data["nodes"]:
            node_key = node_id_encoded
        elif NODE_ID in data["nodes"]:
            node_key = NODE_ID
        elif node_with_colon in data["nodes"]:
            node_key = node_with_colon
        else:
            raise KeyError(f"Node ID not found in any format")

        root_node = data["nodes"][node_key]["document"]
    except KeyError as e:
        print(f"❌ Node не найден в ответе API. Проверь node-id.")
        print(f"   Доступные ключи: {list(data.get('nodes', {}).keys())}")
        return

    result = transform_node(root_node)

    print("\n" + "=" * 50)
    print("SDUI JSON OUTPUT")
    print("=" * 50 + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
