CATEGORIES_URL = "/api/v1/categories/"
LOCATIONS_URL = "/api/v1/locations/"


def create_category(client, headers, **fields):
    payload = {"title": "Категория", "description": "Описание", "slug": "news"}
    payload.update(fields)
    return client.post(CATEGORIES_URL, json=payload, headers=headers)


def test_only_admin_can_create_category(client, create_user, auth_headers):
    create_user("alice")
    create_user("admin", is_admin=True)

    assert create_category(client, auth_headers("alice")).status_code == 403
    assert create_category(client, auth_headers("admin")).status_code == 201


def test_duplicate_slug_is_rejected(client, create_user, auth_headers):
    create_user("admin", is_admin=True)
    headers = auth_headers("admin")
    create_category(client, headers)
    other = create_category(client, headers, slug="other").json()

    create_response = create_category(client, headers)
    update_response = client.patch(
        f"{CATEGORIES_URL}{other['id']}", json={"slug": "news"}, headers=headers
    )
    same_slug_response = client.patch(
        f"{CATEGORIES_URL}{other['id']}", json={"slug": "other"}, headers=headers
    )

    assert create_response.status_code == 409
    assert update_response.status_code == 409
    assert same_slug_response.status_code == 200


def test_category_update_validates_fields(client, create_user, auth_headers):
    create_user("admin", is_admin=True)
    headers = auth_headers("admin")
    category = create_category(client, headers).json()
    url = f"{CATEGORIES_URL}{category['id']}"

    for payload in (
        {"title": None},
        {"title": ""},
        {"title": "   "},
        {"slug": "Not A Slug"},
        {"description": "x" * 10_001},
        {"name": "Категория"},
    ):
        assert client.patch(url, json=payload, headers=headers).status_code == 422
    assert client.put(url, json={"title": "Новая"}, headers=headers).status_code == 405


def test_unpublished_categories_and_locations_are_hidden(
    client, create_user, auth_headers
):
    create_user("admin", is_admin=True)
    headers = auth_headers("admin")
    category = create_category(client, headers, is_published=False).json()
    location = client.post(
        LOCATIONS_URL, json={"name": "Скрытое", "is_published": False}, headers=headers
    ).json()

    assert client.get(CATEGORIES_URL).json() == []
    assert client.get(LOCATIONS_URL).json() == []
    assert client.get(f"{CATEGORIES_URL}{category['id']}").status_code == 404
    assert client.get(f"{LOCATIONS_URL}{location['id']}").status_code == 404
    assert len(client.get(CATEGORIES_URL, headers=headers).json()) == 1
    assert len(client.get(LOCATIONS_URL, headers=headers).json()) == 1


def test_location_update_validates_fields(client, create_user, auth_headers):
    create_user("admin", is_admin=True)
    headers = auth_headers("admin")
    location = client.post(
        LOCATIONS_URL, json={"name": "Москва"}, headers=headers
    ).json()
    url = f"{LOCATIONS_URL}{location['id']}"

    assert client.patch(url, json={"name": None}, headers=headers).status_code == 422
    assert client.patch(url, json={"name": ""}, headers=headers).status_code == 422
    assert client.patch(url, json={"name": "  "}, headers=headers).status_code == 422
    assert (
        client.patch(url, json={"name": "Казань"}, headers=headers).json()["name"]
        == "Казань"
    )


def test_missing_items_return_404(client, create_user, auth_headers):
    create_user("admin", is_admin=True)
    headers = auth_headers("admin")

    assert client.get(f"{CATEGORIES_URL}999").status_code == 404
    assert (
        client.patch(
            f"{LOCATIONS_URL}999", json={"name": "X"}, headers=headers
        ).status_code
        == 404
    )
    assert client.delete(f"{CATEGORIES_URL}999", headers=headers).status_code == 404
