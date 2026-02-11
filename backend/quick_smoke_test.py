import requests
from pprint import pprint

BASE_URL = "http://localhost:8000"


def check_root():
    print("\n1) GET /")
    r = requests.get(f"{BASE_URL}/")
    r.raise_for_status()
    data = r.json()
    pprint(data)
    assert data.get("app") == "Scheme Saathi"


def check_health():
    print("\n2) GET /health")
    r = requests.get(f"{BASE_URL}/health")
    r.raise_for_status()
    data = r.json()
    pprint(data)
    assert data["status"] in ["healthy", "degraded"]
    assert data["total_schemes"] >= 0


def check_chat():
    print("\n3) POST /chat (farmer in Bihar with 2 acres)")
    r = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "I'm a farmer in Bihar with 2 acres",
            "conversation_history": [],
        },
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    print("\nChat reply:")
    print(data["message"])
    print(f"\nFound {len(data['schemes'])} schemes")
    return data


def check_schemes_list():
    print("\n4) GET /schemes?limit=5")
    r = requests.get(f"{BASE_URL}/schemes", params={"limit": 5})
    r.raise_for_status()
    data = r.json()
    print(f"Total returned: {data['total']}")
    print(f"Len(schemes): {len(data['schemes'])}")
    return data


def check_scheme_by_id(scheme_id: str):
    print(f"\n5) GET /schemes/{scheme_id}")
    r = requests.get(f"{BASE_URL}/schemes/{scheme_id}")
    r.raise_for_status()
    data = r.json()
    print(f"Scheme name: {data.get('scheme_name')}")
    return data


if __name__ == "__main__":
    print("=" * 60)
    print("SCHEME SAATHI QUICK SMOKE TEST")
    print("=" * 60)

    try:
        check_root()
        check_health()
        chat_data = check_chat()
        schemes_list = check_schemes_list()

        # Try to fetch first scheme from chat; if none, from list
        scheme_id = None
        if chat_data["schemes"]:
            scheme_id = chat_data["schemes"][0].get("scheme_id")
        elif schemes_list["schemes"]:
            scheme_id = schemes_list["schemes"][0].get("scheme_id")

        if scheme_id:
            check_scheme_by_id(scheme_id)
        else:
            print("\n[WARN] No scheme_id available to test /schemes/{id}")

        print("\n" + "=" * 60)
        print("ALL QUICK CHECKS COMPLETED (no errors).")
        print("=" * 60)
    except Exception as e:
        print("\n" + "=" * 60)
        print("SMOKE TEST FAILED:")
        print(e)
        print("=" * 60)
        raise