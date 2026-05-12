# Python Code Style Guide VINAI HIEPLD (PEP8-based)

## 1. General Principles

-   Code should be readable and consistent.
-   Follow **PEP8** for naming and formatting.
-   A project should use **one consistent style**.

------------------------------------------------------------------------

# 2. Naming Conventions

## 2.1 Class

Classes use **PascalCase**.

``` python
class UserAccount:
    pass

class DataProcessor:
    pass
```

------------------------------------------------------------------------

## 2.2 Variables

Variables use **snake_case**.

``` python
user_name = "Minh"
user_age = 20
total_price = 100
```

Avoid:

``` python
userName
UserName
USERNAME
```

------------------------------------------------------------------------

## 2.3 Functions / Methods

Functions use **snake_case**.

``` python
def get_user_name():
    pass

def calculate_total_price():
    pass
```

------------------------------------------------------------------------

## 2.4 Constants

Constants use **UPPER_CASE**.

``` python
MAX_CONNECTION = 100
DEFAULT_TIMEOUT = 30
API_URL = "https://api.example.com"
```

------------------------------------------------------------------------

## 2.5 Private Variables / Methods

Use a **single underscore**.

``` python
class UserService:

    def __init__(self):
        self._token = None

    def _generate_token(self):
        pass
```

------------------------------------------------------------------------

## 2.6 Special Methods

Use **double underscore** for Python special methods.

``` python
class User:

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name
```

------------------------------------------------------------------------

# 3. File Naming

Files should use **snake_case**.

    user_service.py
    data_processor.py
    config_loader.py

Avoid:

    UserService.py
    dataProcessor.py

------------------------------------------------------------------------

# 4. Class Structure (Recommended Order)

``` python
class UserService:
    MAX_LOGIN = 5

    def __init__(self, name):
        self.name = name
        self._token = None

    def login(self):
        pass

    def logout(self):
        pass

    def _generate_token(self):
        pass
```

Order: 1. Constants 2. `__init__` 3. Public methods 4. Private methods

------------------------------------------------------------------------

# 5. Spacing

### Around operators

Correct:

``` python
total = price + tax
```

Incorrect:

``` python
total=price+tax
```

### After comma

Correct:

``` python
print(name, age)
```

Incorrect:

``` python
print(name,age)
```

------------------------------------------------------------------------

# 6. Line Length

PEP8 base, adjusted for Black:

    <= 88 characters

If longer:

``` python
result = calculate_total_price(
    product_price,
    tax_rate,
    discount
)
```

------------------------------------------------------------------------

# 7. Import Order

Import order:

1.  Standard library
2.  Third‑party packages
3.  Local modules

``` python
import os
import sys

import requests

from app.services import user_service
```

------------------------------------------------------------------------

# 8. Example Code

``` python
MAX_RETRY = 3


class UserAccount:

    def __init__(self, username: str):
        self.username = username
        self._login_attempt = 0

    def login(self):
        if self._login_attempt > MAX_RETRY:
            return False

        self._login_attempt += 1
        return True

    def reset_login(self):
        self._login_attempt = 0
```

------------------------------------------------------------------------

# 9. Recommended Tools

Tools to automatically enforce style:

    black
    flake8
    pylint
    isort

Example:

    black .
    flake8 .
